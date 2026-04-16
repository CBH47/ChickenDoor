
import bluetooth
from micropython import const
import json
 
_IRQ_CENTRAL_CONNECT    = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE        = const(3)
 
_FLAG_READ   = const(0x0002)
_FLAG_WRITE  = const(0x0008)
_FLAG_NOTIFY = const(0x0010)
 
_DOOR_SERVICE_UUID     = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
_CMD_CHAR_UUID         = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")
_STATUS_CHAR_UUID      = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef2")
_DATETIME_CHAR_UUID    = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef3")
_SCHEDULE_CHAR_UUID    = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef4")
_BATTERY_CHAR_UUID     = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef5")
_DEVICE_NAME_CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef6")
_TIMEZONE_CHAR_UUID    = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef7")
_FIRMWARE_CHAR_UUID    = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef8")
_SETTINGS_CHAR_UUID    = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef9")
 
class BLE:
    def __init__(self, command_callback, schedule_callback, datetime_callback):
        self.command_callback  = command_callback
        self.schedule_callback = schedule_callback
        self.datetime_callback = datetime_callback
 
        # stash for device config
        self.device_name = "DoorMotor"
        self.timezone = "UTC"
        self.firmware_version = "1.0.0"
 
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.config(mtu=512)
        self._ble.irq(self._irq)
 
        self._connections = set()
        self._handles = {}
 
        self._register_services()
        self._advertise()
        print("BLE advertising as DoorMotor")
 
    def _register_services(self):
        DOOR_SERVICE = (
            _DOOR_SERVICE_UUID,
            (
                (_CMD_CHAR_UUID,           _FLAG_WRITE),
                (_STATUS_CHAR_UUID,        _FLAG_READ | _FLAG_NOTIFY),
                (_DATETIME_CHAR_UUID,      _FLAG_WRITE),
                (_SCHEDULE_CHAR_UUID,      _FLAG_READ | _FLAG_WRITE),
                (_BATTERY_CHAR_UUID,       _FLAG_READ | _FLAG_NOTIFY),
                (_DEVICE_NAME_CHAR_UUID,   _FLAG_READ | _FLAG_WRITE),
                (_TIMEZONE_CHAR_UUID,      _FLAG_READ | _FLAG_WRITE),
                (_FIRMWARE_CHAR_UUID,      _FLAG_READ),
                (_SETTINGS_CHAR_UUID,      _FLAG_WRITE),
            ),
        )
        ((cmd, status, dt, sched, batt, device_name, timezone, firmware, settings),) = \
            self._ble.gatts_register_services((DOOR_SERVICE,))
 
        self._handles["cmd"]         = cmd
        self._handles["status"]      = status
        self._handles["datetime"]    = dt
        self._handles["schedule"]    = sched
        self._handles["battery"]     = batt
        self._handles["device_name"] = device_name
        self._handles["timezone"]    = timezone
        self._handles["firmware"]    = firmware
        self._handles["settings"]    = settings
        # populate readable chars with default values
        self._ble.gatts_write(self._handles["status"],      b"IDLE")
        self._ble.gatts_write(self._handles["battery"],     b"0.00V")
        self._ble.gatts_write(self._handles["schedule"],    b"[]")
        self._ble.gatts_write(self._handles["device_name"], self.device_name.encode())
        self._ble.gatts_write(self._handles["timezone"],    self.timezone.encode())
        self._ble.gatts_write(self._handles["firmware"],    self.firmware_version.encode())
    def _advertise(self, interval_us=100000):
        name = b"DoorMotor"
        adv_data = (
            bytes([0x02, 0x01, 0x06])
            + bytes([len(name) + 1, 0x09])
            + name
        )
        self._ble.gap_advertise(interval_us, adv_data=adv_data)
 
    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            print(f"Connected: {conn_handle}")
            self.notify_status("CONNECTED")
 
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.discard(conn_handle)
            print(f"Disconnected: {conn_handle}")
            self._advertise()
 
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            try:
                value = self._ble.gatts_read(value_handle).decode().strip()
            except Exception as e:
                print(f"BLE read error: {e}")
                return
 
            if value_handle == self._handles["cmd"]:
                print(f"Command: {value}")
                self.command_callback(value)
 
            elif value_handle == self._handles["datetime"]:
                print(f"DateTime: {value}")
                self.datetime_callback(value)
 
            elif value_handle == self._handles["schedule"]:
                print(f"Schedule: {value}")
                self.schedule_callback(value)
 
            elif value_handle == self._handles["device_name"]:
                print(f"Device name: {value}")
                self.device_name = value
                self._ble.gatts_write(self._handles["device_name"], value.encode())
 
            elif value_handle == self._handles["timezone"]:
                print(f"Timezone: {value}")
                self.timezone = value
                self._ble.gatts_write(self._handles["timezone"], value.encode())
 
            elif value_handle == self._handles["settings"]:
                print(f"Settings command: {value}")
                if value == "RESET":
                    self._reset_settings()
 
    def notify_status(self, status: str):
        encoded = status.encode()
        self._ble.gatts_write(self._handles["status"], encoded)
        for conn in self._connections:
            try:
                self._ble.gatts_notify(conn, self._handles["status"], encoded)
            except Exception as e:
                print(f"Notify error: {e}")
 
    def notify_battery(self, voltage: float):
        payload = f"{voltage:.2f}V".encode()
        self._ble.gatts_write(self._handles["battery"], payload)
        for conn in self._connections:
            try:
                self._ble.gatts_notify(conn, self._handles["battery"], payload)
            except Exception as e:
                print(f"Battery notify error: {e}")
    def update_schedule(self, rules: list):
        payload = json.dumps(rules).encode()
        self._ble.gatts_write(self._handles["schedule"], payload)
 
    def is_connected(self):
        return len(self._connections) > 0
 
    def _reset_settings(self):
        self.device_name = "DoorMotor"
        self.timezone = "UTC"
        self._ble.gatts_write(self._handles["device_name"], self.device_name.encode())
        self._ble.gatts_write(self._handles["timezone"],    self.timezone.encode())
        print("Settings reset to factory defaults")

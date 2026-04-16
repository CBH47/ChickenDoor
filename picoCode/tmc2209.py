
from machine import Pin, UART
import time

class TMC2209:
    def __init__(self):
        #UartSet
        self.uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), txbuf=64, rxbuf=64)

        #Sets control pins
        self.step = Pin(10, Pin.OUT)
        self.dir = Pin(8, Pin.OUT)
        self.en = Pin(4,Pin.OUT)

        #Sets diag as input
        self.diag = Pin(14, Pin.IN, Pin.PULL_DOWN)
        
        #Sets initial conditions
        self.en.value(1)
    
    def sleep(self):
        # Put driver into standby - lowest power state
        self.en.value(1)
    
    def enable(self):
        # Enable motor outputs - motor will hold position
        self.en.value(0)
    
    def disable(self):
        # Disable motor outputs - motor spins freely
        self.en.value(1)
    
    def is_stalled(self):
        # Returns True if DIAG pin is high (stall detected)
        return self.diag.value() == 1
    def _calc_crc(self, data):
        crc = 0
        for byte in data:
            for _ in range(8):
                if (crc >> 7) ^ (byte & 0x01):
                    crc = ((crc << 1) ^ 0x07) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
                byte >>= 1
        return crc
    def _write_register(self, reg, value):
        if self.uart is None:
            return
        data = [
            0x05,        
            0x00,        # slave address
            reg | 0x80,
            (value >> 24) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 8)  & 0xFF,
            (value)       & 0xFF,
        ]
        crc = self._calc_crc(data)
        data.append(crc)
        self.uart.write(bytes(data))
        time.sleep_ms(2)

    def set_hold_run_current(self, ihold, irun, ihold_delay=8):
        return None

    def set_run_mode_current(self):
        return None

    def set_hold_mode_current(self):
        return None

    def set_standstill_delay(self, delay):
        if delay is None:
            return
        delay = max(0, min(255, delay))
        self._write_register(0x11, delay)

    def _read_register(self, reg):
        if self.uart is None:
            return None
        self.uart.read(self.uart.any())
        data = [
            0x05,
            0x00,
            reg,
        ]
        crc = self._calc_crc(data)
        data.append(crc)
        self.uart.write(bytes(data))
        time.sleep_ms(20)
        self.uart.read(4)  # flush echo
        time.sleep_ms(5)
        response = self.uart.read(8)
        return response
    def configure(self):
        """Standard configuration."""
        time.sleep_ms(500)
        self.disable()
        # GCONF=0: SpreadCycle always, no StealthChop velocity-mode switching.
        self._write_register(0x00, 0x00000000)
        time.sleep_ms(100)
        self._write_register(0x6C, 0x10000053)  # CHOPCONF
        time.sleep_ms(100)
        self._write_register(0x70, 0x00050A84)  # PWMCONF
        time.sleep_ms(100)
        self._write_register(0x40, 255)          # GLOBALSCALER: max
        time.sleep_ms(100)
        self._write_register(0x11, 255)          # TPOWERDOWN: max standstill delay
        time.sleep_ms(100)
        # Freeze UART - GPIO-only from here.
        try:
            self.uart.deinit()
        except Exception:
            pass
        self.uart = None
        print("TMC2209 configured")
    
    def configure_high_torque(self):
        """High-torque configuration."""
        time.sleep_ms(500)
        self.disable()
        # GCONF=0: SpreadCycle always, no StealthChop velocity-mode switching.
        self._write_register(0x00, 0x00000000)
        time.sleep_ms(100)
        self._write_register(0x6C, 0x10010004)  # CHOPCONF: SpreadCycle, proven motion
        time.sleep_ms(100)
        self._write_register(0x70, 0x00050A84)  # PWMCONF
        time.sleep_ms(100)
        self._write_register(0x40, 255)          # GLOBALSCALER: max
        time.sleep_ms(100)
        self._write_register(0x11, 255)          # TPOWERDOWN: max standstill delay
        time.sleep_ms(100)
        # Freeze UART - GPIO-only from here.
        try:
            self.uart.deinit()
        except Exception:
            pass
        self.uart = None
        print("TMC2209 configured HIGH TORQUE")

    def read_register_value(self, reg):
        response = self._read_register(reg)
        if response and len(response) == 8:
            return (response[3] << 24) | (response[4] << 16) | (response[5] << 8) | response[6]
        return None

    def _fmt_register_value(self, value):
        if value is None:
            return "None"
        return f"0x{value:08X}"

    def get_runtime_snapshot(self):
        return {
            "en": self.en.value(),
            "diag": self.diag.value(),
            "gconf": self.read_register_value(0x00),
            "gstat": self.read_register_value(0x01),
            "ioin": self.read_register_value(0x06),
            "ihold_irun": self.read_register_value(0x10),
            "chopconf": self.read_register_value(0x6C),
            "drv_status": self.read_register_value(0x6F),
            "pwmconf": self.read_register_value(0x70),
        }

    def log_runtime_snapshot(self, label):
        snapshot = self.get_runtime_snapshot()
        print(
            f"{label}: "
            f"EN={snapshot['en']} "
            f"DIAG={snapshot['diag']} "
            f"GCONF={self._fmt_register_value(snapshot['gconf'])} "
            f"GSTAT={self._fmt_register_value(snapshot['gstat'])} "
            f"IOIN={self._fmt_register_value(snapshot['ioin'])} "
            f"IHOLD_IRUN={self._fmt_register_value(snapshot['ihold_irun'])} "
            f"CHOPCONF={self._fmt_register_value(snapshot['chopconf'])} "
            f"DRV_STATUS={self._fmt_register_value(snapshot['drv_status'])} "
            f"PWMCONF={self._fmt_register_value(snapshot['pwmconf'])}"
        )

    def set_register_value(self, reg, value):
        self._write_register(reg, value)
        time.sleep_ms(100)
        return self.read_register_value(reg)

    def set_chopconf_mres(self, mres):
        current = self.read_register_value(0x6C)
        if current is None:
            return None
        candidate = (current & 0x0FFFFFFF) | ((mres & 0x0F) << 28)
        self._write_register(0x6C, candidate)
        time.sleep_ms(100)
        return self.read_register_value(0x6C)

    def uart_debug(self):
        # Check how many bytes are in the buffer
        print(f"Bytes in buffer before: {self.uart.any()}")
        self.uart.write(bytes([0x55, 0x00, 0x00, 0xE8]))  # raw GCONF read request
        time.sleep_ms(20)
        print(f"Bytes in buffer after: {self.uart.any()}")
        raw = self.uart.read(self.uart.any())
        print(f"Raw bytes received: {raw}")

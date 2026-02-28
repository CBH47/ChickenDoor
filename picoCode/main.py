import time
from tmc2209 import TMC2209
from motor import Motor
from statemachine import StateMachine
from scheduler import Scheduler
from battery import Battery
from ble import BLE
import network
import ntptime

# ── NTP time sync ────────────────────────────────────────────────
def sync_time(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    print("Connecting to WiFi...")
    for _ in range(20):
        if wlan.isconnected():
            print("WiFi connected")
            try:
                ntptime.settime()
                print("Time synced via NTP")
            except Exception as e:
                print(f"NTP failed: {e}")
            wlan.disconnect()
            wlan.active(False)
            return
        time.sleep(1)
    print("WiFi connection failed, time not synced")
    wlan.active(False)

# ── Callbacks from BLE ───────────────────────────────────────────
def on_command(cmd):
    if not sm.can_accept_command():
        print(f"Command ignored, state is {sm.get_state()}")
        return
    if cmd == "OPEN":
        handle_open()
    elif cmd == "CLOSE":
        handle_close()
    else:
        print(f"Unknown command: {cmd}")

def on_schedule(payload):
    # Phone is writing a new schedule as JSON
    try:
        import json
        rules = json.loads(payload)
        sched.rules = rules
        sched.save()
        ble.update_schedule(sched.get_rules())
        print("Schedule updated")
    except Exception as e:
        print(f"Schedule parse error: {e}")

def on_datetime(payload):
    # Phone is setting the time as a Unix timestamp
    try:
        import machine
        ts = int(payload)
        tm = time.gmtime(ts)
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
        print(f"Time set from phone: {tm}")
    except Exception as e:
        print(f"DateTime parse error: {e}")

# ── Motor actions ────────────────────────────────────────────────
def handle_open():
    sm.transition("OPENING")
    ble.notify_status("OPENING")
    result = motor.move(1, motor.max_steps)
    if result == "STALL":
        sm.transition("OPEN")
        ble.notify_status("OPEN")
    elif result == "DONE":
        sm.transition("OPEN")
        ble.notify_status("OPEN")

def handle_close():
    sm.transition("CLOSING")
    ble.notify_status("CLOSING")
    result = motor.move(0, motor.max_steps)
    if result == "STALL":
        sm.transition("CLOSED")
        ble.notify_status("CLOSED")
    elif result == "DONE":
        sm.transition("CLOSED")
        ble.notify_status("CLOSED")

# ── Initialise all layers ────────────────────────────────────────
print("Booting DoorMotor...")

motor = Motor()
motor.driver.configure()
sm    = StateMachine()
sched = Scheduler()
batt  = Battery()
ble   = BLE(on_command, on_schedule, on_datetime)

# ── Try NTP sync ─────────────────────────────────────────────────
# Replace with your WiFi credentials
WIFI_SSID     = "your_ssid"
WIFI_PASSWORD = "your_password"
sync_time(WIFI_SSID, WIFI_PASSWORD)

print("System ready")
ble.notify_status("IDLE")

# ── Main loop ────────────────────────────────────────────────────
last_battery_check = 0

while True:
    # Check scheduler
    action = sched.check()
    if action:
        on_command(action)

    # Check battery every 30 seconds when idle
    if not sm.is_busy() and batt.should_sample():
        voltage = batt.read_voltage()
        status  = batt.get_status()
        ble.notify_battery(voltage)
        if status == "CRITICAL":
            sm.transition("BATTERY_CRITICAL")
            ble.notify_status("BATTERY_CRITICAL")
        elif status == "LOW":
            ble.notify_status("LOW_BATTERY")

    time.sleep_ms(100)
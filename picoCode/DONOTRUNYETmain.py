import time
from tmc2209 import TMC2209
from motor import Motor
from statemachine import StateMachine
from scheduler import Scheduler
from battery import Battery
from ble import BLE
import network
import ntptime

# track when the auto-close timer is supposed to expire
timer_end_time = None

# hook up to wifi and get time from ntp
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
        print(f"Waiting... status: {wlan.status()}")
        time.sleep(1)
    print("WiFi connection failed, time not synced")
    wlan.active(False)

# handling commands that come from the phone
def on_command(cmd):
    global timer_end_time
    
    if cmd == "CONFIG":
        motor.driver.configure()
        ble.notify_status("RECONFIGURED")
        return
    
    # parse and handle timer: "TIMER:minutes" format
    if cmd.startswith("TIMER:"):
        try:
            minutes = int(cmd.split(":")[1])
            if minutes > 0:
                handle_open()
                timer_end_time = time.time() + (minutes * 60)
                print(f"Timer set: door will auto-close in {minutes} minutes")
                return
        except Exception as e:
            print(f"Timer parse error: {e}")
    
    if not sm.can_accept_command():
        print(f"Command ignored, state is {sm.get_state()}")
        return
    if cmd == "OPEN":
        handle_open()
        timer_end_time = None
    elif cmd == "CLOSE":
        handle_close()
        timer_end_time = None
    else:
        print(f"Unknown command: {cmd}")

def on_schedule(payload):
    # phone sent new schedule as json
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
    # phone is giving us the time as unix timestamp
    try:
        import machine
        ts = int(payload)
        tm = time.gmtime(ts)
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
        print(f"Time set from phone: {tm}")
    except Exception as e:
        print(f"DateTime parse error: {e}")

# motor movement stuff
def handle_open():
    sm.transition("OPENING")
    ble.notify_status("OPENING")
    result = motor.move(1, motor.max_steps)
    time.sleep_ms(500)
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
    time.sleep_ms(500)
    if result == "STALL":
        sm.transition("CLOSED")
        ble.notify_status("CLOSED")
    elif result == "DONE":
        sm.transition("CLOSED")
        ble.notify_status("CLOSED")

# fire up all the subsystems
print("Booting DoorMotor...")
time.sleep(3)
motor = Motor()
time.sleep(1)
motor.driver.configure()
sm    = StateMachine()
sched = Scheduler()
batt  = Battery()
ble   = BLE(on_command, on_schedule, on_datetime)

# try to get current time from internet
# TODO: replace with your wifi creds
WIFI_SSID     = "Pixel_9754"
WIFI_PASSWORD = "CBHNCSU47"
try:
    sync_time(WIFI_SSID, WIFI_PASSWORD)
except Exception as e:
    print(f"sync_time crashed: {e}")

print("System ready")
ble.notify_status("IDLE")

# main event loop runs here
last_battery_check = 0

while True:
    # check if scheduler has something for us
    action = sched.check()
    if action:
        on_command(action)

    # if timer is running, check if it expired
    if timer_end_time is not None and time.time() >= timer_end_time:
        print("Timer expired, closing door")
        handle_close()
        timer_end_time = None

    # check battery every 30s when not doing anything
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
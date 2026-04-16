
import time
from tmc2209 import TMC2209
from motor import Motor
from statemachine import StateMachine
from scheduler import Scheduler
from battery import Battery
from ble import BLE
# Set True to run hold-cycle sweep on boot instead of the normal BLE app.
RUN_HOLD_SWEEP_ON_BOOT = False
 
# track when the auto-close timer is supposed to expire
timer_end_time = None
# handling commands that come from the phone
def on_command(cmd, source="Manual"):
    global timer_end_time

    if cmd == "CONFIG":
        ble.notify_status("CONFIG_DISABLED")
        return

    if cmd == "STOP":
        handle_emergency_stop()
        timer_end_time = None
        return
 
    # parse and handle timer: "TIMER:minutes" format
    if cmd.startswith("TIMER:"):
        try:
            minutes = int(cmd.split(":")[1])
            if minutes > 0:
                handle_open("Timer")
                timer_end_time = time.time() + (minutes * 60)
                print(f"Timer set: door will auto-close in {minutes} minutes")
                return
        except Exception as e:
            print(f"Timer parse error: {e}")

    if not sm.can_accept_command():
        print(f"Command ignored, state is {sm.get_state()}")
        return
    
    # Don't reopen if already open, don't reclose if already closed
    if cmd == "OPEN" and sm.get_state() == "OPEN":
        print("Door already open, ignoring OPEN command")
        return
    if cmd == "CLOSE" and sm.get_state() == "CLOSED":
        print("Door already closed, ignoring CLOSE command")
        return
    
    if cmd == "OPEN":
        handle_open(source)
        timer_end_time = None
    elif cmd == "CLOSE":
        handle_close(source)
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
 

def handle_emergency_stop():
    print("Emergency stop")
    motor.stop()
    sm.transition("IDLE")
    ble.notify_status("ESTOP")

def handle_open(reason="Manual"):
    if sm.get_state() in ["OPENING", "OPEN"]:
        print("Open ignored: already open/opening")
        return
    sm.transition("OPENING")
    ble.notify_status("OPENING")
    motor.move(1, motor.max_steps)   # steps, then IDLE
    motor.release()                  # ensure outputs are off at top
    sm.transition("OPEN")
    ble.notify_status("OPEN")

def handle_close(reason="Manual"):
    if sm.get_state() in ["CLOSING", "CLOSED"]:
        print("Close ignored: already closed/closing")
        return
    sm.transition("CLOSING")
    ble.notify_status("CLOSING")
    result = motor.move(0, motor.close_steps)
    print(f"Close result: {result}")
    motor.release()                      # de-energise at bottom
    sm.transition("CLOSED")
    ble.notify_status("CLOSED")

if RUN_HOLD_SWEEP_ON_BOOT:
    print("Booting hold cycle sweep test...")
    time.sleep(2)
    try:
        import hold_cycle_sweep_test as sweep
        sweep.run_all_tests()
    except Exception as e:
        print(f"Sweep boot run failed: {e}")

    print("Sweep finished. Idling.")
    while True:
        time.sleep(1)
 
# fire up all the subsystems
print("Booting DoorMotor...")
time.sleep(3)
motor = Motor(high_torque=True)
time.sleep(1)
# motor.driver.configure()  # Already done in Motor.__init__
sm    = StateMachine()
sched = Scheduler()
batt  = Battery()
ble   = BLE(on_command, on_schedule, on_datetime)

print("System ready")
ble.notify_status("IDLE")
 
# main event loop
while True:
    # check if scheduler has something for us
    action = sched.check()
    if action:
        on_command(action, "Schedule")
 
    # if timer is running, check if it expired
    if timer_end_time is not None and time.time() >= timer_end_time:
        print("Timer expired, closing door")
        handle_close("Timer")
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
 
    time.sleep_ms(50)
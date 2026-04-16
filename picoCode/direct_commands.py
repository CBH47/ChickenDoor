# Direct REPL commands for testing (no files needed)

# Check current motor state:
import __main__ as m; print("Enable pin:", m.motor.driver.en.value())

# Engage hold:
import __main__ as m; m.motor.hold(); print("Hold engaged")

# Monitor for 10 seconds:
for i in range(10): import __main__ as m; print(f"Enable: {m.motor.driver.en.value()}"); import time; time.sleep(1)

# Direct pin control (bypass motor class):
from machine import Pin; en=Pin(4, Pin.OUT); en.value(0); print("Direct hold engaged")

# Monitor direct pin:
for i in range(10): from machine import Pin; en=Pin(4, Pin.OUT); print(f"Direct enable: {en.value()}"); import time; time.sleep(1)

# Stop direct control:
from machine import Pin; en=Pin(4, Pin.OUT); en.value(1); print("Direct control stopped")

# Test move:
import __main__ as m; result = m.motor.move(1, 50); print("Move result:", result)

# Check after move:
import __main__ as m; print("After move enable:", m.motor.driver.en.value())
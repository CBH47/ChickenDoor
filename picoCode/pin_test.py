"""
Ultra-minimal pin test - bypass all motor classes
"""

from machine import Pin
import time

print("Ultra-minimal pin test starting...")

# Directly control the enable pin (same as TMC2209 uses)
en_pin = Pin(4, Pin.OUT)
en_pin.value(0)  # Enable motor (hold)
print("Motor enabled directly via pin - should hold continuously")

print("Test running... Press Ctrl+C to stop")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Test stopped")
    en_pin.value(1)  # Disable motor
    print("Motor disabled")
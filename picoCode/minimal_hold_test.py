"""
Minimal hold test - just engage hold and do nothing else
"""

import time
from motor import Motor

print("Minimal hold test starting...")

# Initialize motor
motor = Motor()
print("Motor initialized")

# Engage hold once
motor.hold()
print("Hold engaged - motor should stay on continuously")

# Do nothing - just let it hold
print("Test running... Press Ctrl+C to stop")
try:
    while True:
        time.sleep(1)  # Just sleep, don't check pin state
except KeyboardInterrupt:
    print("Test stopped")
    motor.stop()
    print("Motor stopped")
"""
Test file for motor hold functionality
Energizes the motor at maximum holding current so you can test if it's strong enough
to hold the door in the open position against resistance.
"""

import time
from motor import Motor

print("=" * 50)
print("MOTOR HOLD TEST")
print("=" * 50)

# Initialize motor
print("Initializing motor...")
motor = Motor()
print("Motor initialized")

# Engage hold
print("\nEngaging hold...")
motor.hold()

# Hold for test duration
hold_duration_seconds = 300  # 5 minutes
print(f"Motor is now holding. Test duration: {hold_duration_seconds} seconds")
print(f"Try to push/pull the door to test hold strength")
print(f"Press Ctrl+C to stop the test\n")

try:
    # Keep the motor energized during the hold test
    for i in range(hold_duration_seconds):
        remaining = hold_duration_seconds - i
        if remaining % 30 == 0 or remaining <= 5:
            print(f"Hold active... {remaining} seconds remaining")
        time.sleep(1)
    
    print("\nTest duration complete!")
    
except KeyboardInterrupt:
    print("\nTest interrupted by user")

# Release hold
print("Releasing hold...")
motor.stop()
print("Motor de-energized. Test complete.")
print("=" * 50)

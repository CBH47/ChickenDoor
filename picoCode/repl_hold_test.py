"""
Simple REPL commands for motor hold testing
Copy and paste these commands directly into the REPL
"""

# REPL TEST COMMANDS:
"""
# 1. Import and initialize
from motor import Motor
motor = Motor()

# 2. Check initial state
print("Enable pin value:", motor.driver.en.value())  # Should be 1 (disabled)

# 3. Engage hold
motor.hold()
print("After hold - Enable pin:", motor.driver.en.value())  # Should be 0 (enabled)

# 4. Monitor hold continuously
while True:
    print("Enable pin:", motor.driver.en.value(), "Time:", time.time())
    time.sleep(0.5)

# 5. Test move then hold
motor.move(1, 100)  # Short move
print("After move - Enable pin:", motor.driver.en.value())  # Should be 0

# 6. Stop when done
motor.stop()
print("After stop - Enable pin:", motor.driver.en.value())  # Should be 1
"""
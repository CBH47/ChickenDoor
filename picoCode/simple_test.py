"""
Simple hold test that works alongside running main.py
"""

import time

def simple_hold_test():
    """Test hold by directly controlling the enable pin"""

    print("Simple hold test starting...")

    # Get access to the running motor
    import __main__ as m
    motor = m.motor

    print(f"Initial enable state: {motor.driver.en.value()}")

    # Override the hold method temporarily
    original_hold = motor.hold

    def test_hold():
        print("Test hold called")
        motor.driver.en.value(0)  # Enable motor
        print("Motor enabled for holding")

    motor.hold = test_hold

    # Test hold
    motor.hold()

    # Monitor for 15 seconds
    print("Monitoring hold for 15 seconds...")
    for i in range(15):
        state = motor.driver.en.value()
        print(f"Second {i+1}: Enable = {state} {'(HOLDING)' if state == 0 else '(DROPPED!)'}")
        time.sleep(1)

    # Restore original method
    motor.hold = original_hold
    print("Original hold method restored")

# Run the test
simple_hold_test()
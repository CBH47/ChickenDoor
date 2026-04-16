"""
Test that can run alongside main.py without stopping it
This injects test code into the running system
"""

import time

def test_hold_injection():
    """Test hold functionality by accessing the existing motor instance"""

    print("Hold injection test starting...")

    # Try to access the existing motor instance
    try:
        import __main__ as main_module
        if hasattr(main_module, 'motor'):
            motor = main_module.motor
            print("Found existing motor instance")

            # Save current state
            original_state = motor.driver.en.value()
            print(f"Original enable state: {original_state}")

            # Test hold
            print("Engaging hold...")
            motor.hold()

            # Monitor for 10 seconds
            print("Monitoring hold for 10 seconds...")
            for i in range(10):
                current_state = motor.driver.en.value()
                print(f"Second {i+1}: Enable = {current_state} {'(HOLDING)' if current_state == 0 else '(DROPPED!)'}")
                time.sleep(1)

            print("Test complete - motor should still be holding")
            return True

        else:
            print("No existing motor instance found")
            return False

    except Exception as e:
        print(f"Error accessing motor: {e}")
        return False

# Run the test
if __name__ == "__main__":
    test_hold_injection()
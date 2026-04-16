"""
Test that temporarily disables main loop for testing
"""

import time

def run_isolated_test():
    """Run test with main loop disabled"""

    print("Isolated motor test starting...")

    try:
        # Enable testing mode to disable main loop
        import __main__ as main_module
        main_module.testing_mode = True
        print("Testing mode enabled - main loop disabled")

        # Get the existing motor instance
        motor = main_module.motor
        print("Using existing motor instance")

        # Test 1: Check current state
        initial_state = motor.driver.en.value()
        print(f"Initial enable state: {initial_state}")

        # Test 2: Engage hold
        print("Engaging hold...")
        motor.hold()
        hold_state = motor.driver.en.value()
        print(f"After hold - enable state: {hold_state} (should be 0)")

        # Test 3: Monitor for cycling
        print("Monitoring for 20 seconds...")
        cycling_detected = False
        last_state = hold_state

        for i in range(20):
            current_state = motor.driver.en.value()
            if current_state != last_state:
                print(f"STATE CHANGE at second {i+1}: {last_state} -> {current_state}")
                cycling_detected = True
                last_state = current_state

            if i % 5 == 0:  # Print every 5 seconds
                print(f"Second {i+1}: Enable = {current_state}")

            time.sleep(1)

        if cycling_detected:
            print("❌ CYCLING DETECTED!")
        else:
            print("✅ No cycling detected - hold is stable")

        # Test 4: Test move then hold
        print("\nTesting move then hold...")
        result = motor.move(1, 50)  # Short move
        print(f"Move result: {result}")
        move_state = motor.driver.en.value()
        print(f"After move - enable state: {move_state} (should be 0)")

        # Monitor after move
        print("Monitoring after move for 10 seconds...")
        for i in range(10):
            current_state = motor.driver.en.value()
            print(f"Second {i+1}: Enable = {current_state}")
            time.sleep(1)

        print("Test complete")

    except Exception as e:
        print(f"Test error: {e}")

    finally:
        # Always re-enable main loop
        try:
            main_module.testing_mode = False
            print("Testing mode disabled - main loop re-enabled")
        except:
            print("Could not re-enable main loop")

# Run the test
if __name__ == "__main__":
    run_isolated_test()
"""
Comprehensive motor hold diagnostic test
Run this from REPL to debug hold cycling issues
"""

import time
from motor import Motor
from machine import Pin

def test_hold_diagnostics():
    print("=" * 60)
    print("MOTOR HOLD DIAGNOSTIC TEST")
    print("=" * 60)

    # Initialize motor
    print("Initializing motor...")
    motor = Motor()
    print("Motor initialized")

    # Get direct access to enable pin for monitoring
    en_pin = motor.driver.en
    print(f"Enable pin object: {en_pin}")
    print(f"Enable pin value (1=disabled, 0=enabled): {en_pin.value()}")

    # Test 1: Basic hold functionality
    print("\n" + "=" * 40)
    print("TEST 1: Basic Hold Function")
    print("=" * 40)

    print("Calling motor.hold()...")
    motor.hold()
    print(f"After hold() - Enable pin: {en_pin.value()} (should be 0)")

    # Monitor hold for 10 seconds
    print("Monitoring hold for 10 seconds...")
    for i in range(10):
        pin_state = en_pin.value()
        print(f"Second {i+1}: Enable pin = {pin_state} {'(HOLDING)' if pin_state == 0 else '(NOT HOLDING)'}")
        time.sleep(1)

    # Test 2: Move then hold
    print("\n" + "=" * 40)
    print("TEST 2: Move Then Hold")
    print("=" * 40)

    print("Testing short move (50 steps)...")
    result = motor.move(1, 50)  # Short move to test
    print(f"Move result: {result}")
    print(f"After move - Enable pin: {en_pin.value()} (should be 0 for holding)")

    # Monitor for 10 seconds
    print("Monitoring after move for 10 seconds...")
    for i in range(10):
        pin_state = en_pin.value()
        print(f"Second {i+1}: Enable pin = {pin_state} {'(HOLDING)' if pin_state == 0 else '(NOT HOLDING)'}")
        time.sleep(1)

    # Test 3: Manual hold strength test
    print("\n" + "=" * 40)
    print("TEST 3: Manual Hold Strength Test")
    print("=" * 40)

    print("Engaging hold for manual testing...")
    motor.hold()
    print(f"Enable pin: {en_pin.value()} (should be 0)")
    print("Try to move the door manually now!")
    print("Press Ctrl+C when done testing")

    try:
        while True:
            pin_state = en_pin.value()
            print(f"Hold active - Enable pin: {pin_state} {'(HOLDING)' if pin_state == 0 else '(DROPPED!)'}")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nManual test interrupted")

    # Test 4: Stop test
    print("\n" + "=" * 40)
    print("TEST 4: Stop Function")
    print("=" * 40)

    print("Calling motor.stop()...")
    motor.stop()
    print(f"After stop() - Enable pin: {en_pin.value()} (should be 1)")

    print("\n" + "=" * 60)
    print("DIAGNOSTIC TEST COMPLETE")
    print("Check the output above for any pin state changes")
    print("If pin goes from 0 to 1 unexpectedly, that's the cycling issue")
    print("=" * 60)

def quick_hold_test():
    """Quick test - just engage hold and monitor"""
    print("Quick hold test - Ctrl+C to stop")
    motor = Motor()
    motor.hold()
    en_pin = motor.driver.en

    try:
        while True:
            print(f"Enable pin: {en_pin.value()} (0=holding, 1=not holding)")
            time.sleep(1)
    except KeyboardInterrupt:
        motor.stop()
        print("Test stopped")

# Run the full diagnostic
if __name__ == "__main__":
    test_hold_diagnostics()
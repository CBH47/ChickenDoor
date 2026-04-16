"""
Test using the existing motor instance from main.py
This avoids creating a new Motor object that might interfere
"""

import time

print("Testing with existing motor instance...")

# Try to access the global motor instance from main.py
try:
    # This assumes main.py has already run and created the 'motor' global
    import sys
    main_module = sys.modules.get('__main__')
    if main_module and hasattr(main_module, 'motor'):
        motor = main_module.motor
        print("Using existing motor instance from main.py")
    else:
        print("Could not find existing motor instance, creating new one")
        from motor import Motor
        motor = Motor()

    # Test hold
    print("Engaging hold...")
    motor.hold()
    print("Hold engaged - monitoring for 30 seconds")

    # Monitor for 30 seconds
    for i in range(30):
        pin_state = motor.driver.en.value()
        print(f"Second {i+1}: Enable pin = {pin_state} {'(HOLDING)' if pin_state == 0 else '(DROPPED!)'}")
        time.sleep(1)

    print("Test complete")

except Exception as e:
    print(f"Error: {e}")
    print("Falling back to direct pin control...")

    # Fallback: direct pin control
    from machine import Pin
    en_pin = Pin(4, Pin.OUT)
    en_pin.value(0)  # Enable
    print("Direct pin control - holding for 30 seconds")

    for i in range(30):
        print(f"Second {i+1}: Holding")
        time.sleep(1)

    en_pin.value(1)  # Disable
    print("Test complete")
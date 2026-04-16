"""
Aggressive 1/16 Microstep Speed Test

This test fixes the TMC2209 to true 1/16 microstep mode and
runs the aggressive 600µs step delay sequence.
"""

from motor import Motor
import time


def print_value(label, value):
    if value is None:
        print(f"{label}: None")
    else:
        print(f"{label}: 0x{value:08X}")


def run_aggressive_1_16_test():
    print("""
AGGRESSIVE 1/16 MICROSTEP TEST
==============================

This test configures the driver to true 1/16 microstep mode and
runs 5 segments of 400 steps at 600µs step delay.
""")

    motor = Motor(high_torque=False)
    driver = motor.driver
    time.sleep_ms(500)

    baseline = driver.read_register_value(0x6C)
    print_value("Baseline CHOPCONF", baseline)
    if baseline is None:
        print("Unable to read CHOPCONF. Aborting.")
        return

    print("Setting true microstep mode to 1/16...")
    actual = driver.set_chopconf_mres(4)
    print_value("CHOPCONF after 1/16 set", actual)
    if actual is None:
        print("Failed to set 1/16 microstep mode. Aborting.")
        return

    motor.step_delay_us = 600
    print("\nStarting aggressive 600µs test (833 Hz) using 1/16 microstep...")

    for segment in range(5):
        print(f"Segment {segment + 1}/5")
        motor.move(1, 400)
        time.sleep_ms(200)

    print("\nRestoring original CHOPCONF")
    driver.set_register_value(0x6C, baseline)
    print("1/16 aggressive speed test complete")


if __name__ == '__main__':
    run_aggressive_1_16_test()

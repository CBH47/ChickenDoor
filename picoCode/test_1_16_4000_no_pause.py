"""
1/32 Microstep 4000-Step No-Pause Test

This test configures the TMC2209 to true 1/32 microstep mode and
runs a continuous 4000-step move with no extra pause between segments.
"""

from motor import Motor
import time


def print_value(label, value):
    if value is None:
        print(f"{label}: None")
    else:
        print(f"{label}: 0x{value:08X}")


def run_long_no_pause_test():
    print("""
1/32 MICROSTEP 4000-STEP NO-PAUSE TEST
=====================================

This test uses true 1/32 microstep mode and executes a single
continuous 4000-step move.
""")

    motor = Motor(high_torque=False)
    driver = motor.driver
    time.sleep_ms(500)

    baseline = driver.read_register_value(0x6C)
    print_value("Baseline CHOPCONF", baseline)
    if baseline is None:
        print("Unable to read CHOPCONF. Aborting.")
        return

    print("Setting true microstep mode to 1/32...")
    actual = driver.set_chopconf_mres(3)
    print_value("CHOPCONF after 1/32 set", actual)
    if actual is None:
        print("Failed to set 1/32 microstep mode. Aborting.")
        return

    motor.step_delay_us = 150
    print("\nStarting continuous 4000-step move with no pauses...")
    motor.move(1, 4250)

    print("\nRestoring original CHOPCONF")
    driver.set_register_value(0x6C, baseline)
    print("1/32 4000-step no-pause test complete")


if __name__ == '__main__':
    run_long_no_pause_test()

"""
1/16 Microstep Speed Comparison

This test fixes the driver to true 1/16 microstep mode and then
compares different step delay settings to find the best torque/smoothness tradeoff.
"""

from motor import Motor
import time

configs = [
    ("SLOW (1500µs - 333 Hz)", 1500),
    ("ORIGINAL (1200µs - 416 Hz)", 1200),
    ("MEDIUM (1000µs - 500 Hz)", 1000),
    ("FAST (800µs - 625 Hz)", 800),
    ("AGGRESSIVE (600µs - 833 Hz)", 600),
]


def print_value(label, value):
    if value is None:
        print(f"{label}: None")
    else:
        print(f"{label}: 0x{value:08X}")


def run_speed_test_with_1_16():
    print("""
1/16 MICROSTEP SPEED TEST
=========================

This test configures the TMC2209 to true 1/16 microstep mode,
then exercises a set of step delays to see which speed gives the
best torque and smooth operation.
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

    print("Starting speed comparison with 1/16 microstep...")
    for name, delay_us in configs:
        print("\n" + "=" * 60)
        print(f"Testing: {name}")
        print(f"Step delay: {delay_us}µs")
        print(f"Target frequency: {1_000_000 / (2 * delay_us):.0f} Hz")
        print("=" * 60)

        motor.step_delay_us = delay_us
        for segment in range(5):
            print(f"Segment {segment + 1}/5")
            motor.move(1, 400)
            time.sleep_ms(200)

        time.sleep_ms(500)

    print("\nRestoring original CHOPCONF")
    driver.set_register_value(0x6C, baseline)
    print("1/16 speed comparison complete")


if __name__ == '__main__':
    run_speed_test_with_1_16()

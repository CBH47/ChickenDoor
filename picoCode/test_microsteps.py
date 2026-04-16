"""
Microstep Mode Comparison
Compare baseline CHOPCONF with low-microstep alternatives.
"""

from motor import Motor
import time


def print_value(label, value):
    if value is None:
        print(f"{label}: None")
    else:
        print(f"{label}: 0x{value:08X}")


def run_microstep_comparison():
    print("""
MICROSTEP MODE COMPARISON
========================
This test compares the current baseline CHOPCONF value with
lower-microstep CHOPCONF modes.

The script will:
 1. configure the driver
 2. read back baseline CHOPCONF
 3. test 1/16-step
 4. test full-step
""")

    motor = Motor(high_torque=False)
    driver = motor.driver
    time.sleep_ms(500)

    baseline = driver.read_register_value(0x6C)
    print_value("Baseline CHOPCONF", baseline)
    if baseline is None:
        print("Unable to read CHOPCONF. Aborting.")
        return

    candidates = [
        (4, "1/16 step"),
        (8, "full step"),
    ]

    for mres, label in candidates:
        print("\n" + "="*60)
        print(f"Testing {label} (MRES={mres})")
        print("="*60)

        actual = driver.set_chopconf_mres(mres)
        print_value("CHOPCONF after write", actual)
        if actual is None:
            print("Write or readback failed. Skipping test.")
            continue

        # Run 5 segments of 400 steps each to expose mid-run torque loss.
        for segment in range(5):
            print(f"Segment {segment + 1}/5")
            motor.step_delay_us = 1200
            result = motor.move(1, 400)
            print(result)
            time.sleep_ms(200)

        print("Restoring baseline CHOPCONF")
        driver.set_chopconf_mres((baseline >> 24) & 0x0F)
        time.sleep_ms(200)

    print("\n" + "="*60)
    print("MICROSTEP COMPARISON COMPLETE")
    print("="*60)


if __name__ == '__main__':
    run_microstep_comparison()

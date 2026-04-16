"""
Simple TMC2209 current-control verification test.

Run from REPL:
    import test_current_control

This checks whether UART writes to:
- IHOLD_IRUN (0x10)
- GLOBALSCALER (0x40)
- CHOPCONF (0x6C)
actually stick on the connected module.
"""

import time
from tmc2209 import TMC2209


def fmt(value):
    if value is None:
        return "None"
    return f"0x{value:08X}"


def verify_register(driver, reg, value, label, delay_ms=100):
    print(f"\nTesting {label}")
    print(f"  Writing {fmt(value)} to register 0x{reg:02X}")
    driver._write_register(reg, value)
    time.sleep_ms(delay_ms)
    actual = driver.read_register_value(reg)
    print(f"  Readback: {fmt(actual)}")
    success = actual == value
    print(f"  Result: {'PASS' if success else 'FAIL'}")
    return success, actual


def run():
    print("=" * 60)
    print("TMC2209 CURRENT CONTROL VERIFICATION")
    print("=" * 60)

    driver = TMC2209()
    driver.configure_high_torque()
    driver.enable()
    time.sleep_ms(100)

    print("\nInitial register state:")
    print(f"  GCONF:       {fmt(driver.read_register_value(0x00))}")
    print(f"  IHOLD_IRUN:  {fmt(driver.read_register_value(0x10))}")
    print(f"  GLOBALSCALER:{fmt(driver.read_register_value(0x40))}")

    ihold_test_value = 0x00080505
    scaler_test_value = 0x00000080
    chopconf_before = driver.read_register_value(0x6C)
    chopconf_test_value = None
    if chopconf_before is not None:
        # Toggle MRES bits only, leaving the rest of CHOPCONF untouched.
        current_mres = (chopconf_before >> 24) & 0x0F
        test_mres = 4 if current_mres != 4 else 3
        chopconf_test_value = (chopconf_before & 0xF0FFFFFF) | (test_mres << 24)

    ihold_ok, _ = verify_register(driver, 0x10, ihold_test_value, "IHOLD_IRUN")
    scaler_ok, _ = verify_register(driver, 0x40, scaler_test_value, "GLOBALSCALER")
    if chopconf_test_value is not None:
        chopconf_ok, _ = verify_register(driver, 0x6C, chopconf_test_value, "CHOPCONF")
    else:
        chopconf_ok = False
        print("\nTesting CHOPCONF")
        print("  Readback unavailable, skipping")

    print("\nRestoring full-scale settings...")
    driver._write_register(0x10, 0x00081F1F)
    time.sleep_ms(100)
    driver._write_register(0x40, 0x000000FF)
    time.sleep_ms(100)
    if chopconf_before is not None:
        driver._write_register(0x6C, chopconf_before)
        time.sleep_ms(100)

    print(f"  Restored IHOLD_IRUN:   {fmt(driver.read_register_value(0x10))}")
    print(f"  Restored GLOBALSCALER: {fmt(driver.read_register_value(0x40))}")
    print(f"  Restored CHOPCONF:     {fmt(driver.read_register_value(0x6C))}")

    print("\nSummary:")
    print(f"  IHOLD_IRUN writable:   {ihold_ok}")
    print(f"  GLOBALSCALER writable: {scaler_ok}")
    print(f"  CHOPCONF writable:     {chopconf_ok}")

    if ihold_ok and scaler_ok and chopconf_ok:
        print("  Conclusion: UART current control and mode control are working.")
    elif chopconf_ok:
        print("  Conclusion: UART communication works for mode registers, but current control does not.")
    else:
        print("  Conclusion: UART current control is NOT working on this module/config.")
        print("  Hold torque is likely controlled by hardware VREF/current limit instead.")

    driver.disable()
    print("\nDriver disabled. Test complete.")


run()
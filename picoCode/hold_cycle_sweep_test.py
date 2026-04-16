from tmc2209 import TMC2209
import time

# Structured sweep to isolate hold-cycling triggers.
# Sequence runs from simple to complex with a fixed 5s pause between tests.
#
# Usage on Pico REPL:
#   import hold_cycle_sweep_test as sweep
#   sweep.run_all_tests()

# Registers
REG_GCONF = 0x00
REG_CHOPCONF = 0x6C
REG_PWMCONF = 0x70
REG_GLOBALSCALER = 0x40
REG_TPOWERDOWN = 0x11

# Known working-ish defaults
BASE_GCONF = 0x00000000      # SpreadCycle only
BASE_CHOPCONF = 0x10010004   # high torque profile
BASE_PWMCONF = 0x00050A84
BASE_GLOBALSCALER = 255
BASE_TPOWERDOWN = 255

MOVE_STEPS = 5500
MOVE_DIR_UP = 1

HOLD_SECONDS = 8
PAUSE_BETWEEN_TESTS_SECONDS = 5


def _fmt_params(params):
    keys = sorted(params.keys())
    parts = []
    for k in keys:
        parts.append("%s=%s" % (k, params[k]))
    return ", ".join(parts)


def _safe_uart_deinit(drv):
    try:
        if drv.uart is not None:
            drv.uart.deinit()
    except Exception:
        pass


def _sleep_seconds_with_countdown(seconds):
    for sec in range(seconds, 0, -1):
        print("  next test in %ds" % sec)
        time.sleep(1)


def _apply_registers(drv, cfg):
    # Keep this raw and explicit; avoid configure()/configure_high_torque()
    # because those freeze UART in current project code.
    drv.disable()
    time.sleep_ms(250)

    drv._write_register(REG_GCONF, cfg.get("gconf", BASE_GCONF))
    time.sleep_ms(30)
    drv._write_register(REG_CHOPCONF, cfg.get("chopconf", BASE_CHOPCONF))
    time.sleep_ms(30)
    drv._write_register(REG_PWMCONF, cfg.get("pwmconf", BASE_PWMCONF))
    time.sleep_ms(30)
    drv._write_register(REG_GLOBALSCALER, cfg.get("globalscaler", BASE_GLOBALSCALER))
    time.sleep_ms(30)
    drv._write_register(REG_TPOWERDOWN, cfg.get("tpowerdown", BASE_TPOWERDOWN))
    time.sleep_ms(30)


def _move_up(drv, steps, step_delay_us):
    drv.enable()
    drv.dir.value(MOVE_DIR_UP)
    time.sleep_ms(5)

    for _ in range(steps):
        drv.step.value(1)
        time.sleep_us(step_delay_us)
        drv.step.value(0)
        time.sleep_us(step_delay_us)


def _hold_en_only(drv, hold_seconds):
    deadline = time.ticks_add(time.ticks_ms(), hold_seconds * 1000)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        drv.enable()
        time.sleep_ms(20)


def _hold_reassert_en(drv, hold_seconds, reassert_ms):
    deadline = time.ticks_add(time.ticks_ms(), hold_seconds * 1000)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        drv.enable()
        time.sleep_ms(reassert_ms)


def _hold_dither_one_way(drv, hold_seconds, interval_ms, pulse_us):
    deadline = time.ticks_add(time.ticks_ms(), hold_seconds * 1000)
    drv.dir.value(MOVE_DIR_UP)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        drv.enable()
        drv.step.value(1)
        time.sleep_us(pulse_us)
        drv.step.value(0)
        time.sleep_ms(interval_ms)


def _hold_dither_alternating(drv, hold_seconds, interval_ms, pulse_us):
    deadline = time.ticks_add(time.ticks_ms(), hold_seconds * 1000)
    d = 0
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        drv.enable()
        d ^= 1
        drv.dir.value(d)
        drv.step.value(1)
        time.sleep_us(pulse_us)
        drv.step.value(0)
        time.sleep_ms(interval_ms)


def _run_case(case_index, total_cases, case_name, cfg, behavior):
    print("\n==============================")
    print("TEST %d/%d" % (case_index, total_cases))
    print("name: %s" % case_name)
    print("registers: %s" % _fmt_params(cfg))
    print("behavior: %s" % _fmt_params(behavior))
    print("==============================")

    drv = TMC2209()

    try:
        _apply_registers(drv, cfg)

        steps = behavior.get("steps", MOVE_STEPS)
        step_delay_us = behavior.get("step_delay_us", 300)
        hold_mode = behavior.get("hold_mode", "en_only")
        hold_seconds = behavior.get("hold_seconds", HOLD_SECONDS)

        print("  moving up: steps=%d, step_delay_us=%d" % (steps, step_delay_us))
        _move_up(drv, steps, step_delay_us)
        print("  move done, starting hold mode: %s" % hold_mode)

        if hold_mode == "en_only":
            _hold_en_only(drv, hold_seconds)
        elif hold_mode == "reassert_en":
            _hold_reassert_en(drv, hold_seconds, behavior.get("reassert_ms", 20))
        elif hold_mode == "dither_one_way":
            _hold_dither_one_way(
                drv,
                hold_seconds,
                behavior.get("dither_interval_ms", 20),
                behavior.get("dither_pulse_us", 4),
            )
        elif hold_mode == "dither_alternating":
            _hold_dither_alternating(
                drv,
                hold_seconds,
                behavior.get("dither_interval_ms", 20),
                behavior.get("dither_pulse_us", 4),
            )
        else:
            print("  unknown hold mode: %s" % hold_mode)

        drv.disable()
        print("  test complete")

    except Exception as e:
        print("  test error: %s" % e)
        try:
            drv.disable()
        except Exception:
            pass
    finally:
        _safe_uart_deinit(drv)


def build_test_plan():
    base_cfg = {
        "gconf": BASE_GCONF,
        "chopconf": BASE_CHOPCONF,
        "pwmconf": BASE_PWMCONF,
        "globalscaler": BASE_GLOBALSCALER,
        "tpowerdown": BASE_TPOWERDOWN,
    }

    tests = []

    # Phase 1: Ground-up hold behaviors.
    tests.append((
        "baseline_en_only",
        dict(base_cfg),
        {"hold_mode": "en_only", "steps": MOVE_STEPS, "step_delay_us": 300, "hold_seconds": HOLD_SECONDS},
    ))
    tests.append((
        "baseline_reassert_en_20ms",
        dict(base_cfg),
        {"hold_mode": "reassert_en", "reassert_ms": 20, "steps": MOVE_STEPS, "step_delay_us": 300, "hold_seconds": HOLD_SECONDS},
    ))
    tests.append((
        "dither_one_way_20ms_4us",
        dict(base_cfg),
        {"hold_mode": "dither_one_way", "dither_interval_ms": 20, "dither_pulse_us": 4, "steps": MOVE_STEPS, "step_delay_us": 300, "hold_seconds": HOLD_SECONDS},
    ))
    tests.append((
        "dither_alternating_20ms_4us",
        dict(base_cfg),
        {"hold_mode": "dither_alternating", "dither_interval_ms": 20, "dither_pulse_us": 4, "steps": MOVE_STEPS, "step_delay_us": 300, "hold_seconds": HOLD_SECONDS},
    ))

    # Phase 2: TPOWERDOWN sweep with one-way dither.
    for tpd in [0, 1, 8, 32, 255]:
        cfg = dict(base_cfg)
        cfg["tpowerdown"] = tpd
        tests.append((
            "tpowerdown_%d_one_way_dither" % tpd,
            cfg,
            {"hold_mode": "dither_one_way", "dither_interval_ms": 20, "dither_pulse_us": 4, "steps": MOVE_STEPS, "step_delay_us": 300, "hold_seconds": HOLD_SECONDS},
        ))

    # Phase 3: GCONF/CHOPCONF combinations.
    combo_cfgs = [
        (0x00000000, 0x10010004, "g0_chop_high_torque"),
        (0x00000000, 0x10000053, "g0_chop_standard"),
        (0x00000004, 0x10010004, "g4_chop_high_torque"),
        (0x00000004, 0x10000053, "g4_chop_standard"),
    ]
    for gconf, chopconf, label in combo_cfgs:
        cfg = dict(base_cfg)
        cfg["gconf"] = gconf
        cfg["chopconf"] = chopconf
        tests.append((
            label,
            cfg,
            {"hold_mode": "dither_one_way", "dither_interval_ms": 20, "dither_pulse_us": 4, "steps": MOVE_STEPS, "step_delay_us": 300, "hold_seconds": HOLD_SECONDS},
        ))

    # Phase 4: Motion and dither timing sweeps.
    for delay in [200, 300, 600]:
        tests.append((
            "step_delay_%dus" % delay,
            dict(base_cfg),
            {"hold_mode": "dither_one_way", "dither_interval_ms": 20, "dither_pulse_us": 4, "steps": MOVE_STEPS, "step_delay_us": delay, "hold_seconds": HOLD_SECONDS},
        ))

    for interval_ms in [10, 20, 40, 80]:
        tests.append((
            "dither_interval_%dms" % interval_ms,
            dict(base_cfg),
            {"hold_mode": "dither_one_way", "dither_interval_ms": interval_ms, "dither_pulse_us": 4, "steps": MOVE_STEPS, "step_delay_us": 300, "hold_seconds": HOLD_SECONDS},
        ))

    for pulse_us in [2, 4, 8, 16]:
        tests.append((
            "dither_pulse_%dus" % pulse_us,
            dict(base_cfg),
            {"hold_mode": "dither_one_way", "dither_interval_ms": 20, "dither_pulse_us": pulse_us, "steps": MOVE_STEPS, "step_delay_us": 300, "hold_seconds": HOLD_SECONDS},
        ))

    return tests


def run_all_tests():
    tests = build_test_plan()
    total = len(tests)

    print("\nHold Cycling Sweep Start")
    print("total tests: %d" % total)
    print("hold seconds per test: %d" % HOLD_SECONDS)
    print("pause between tests: %d" % PAUSE_BETWEEN_TESTS_SECONDS)
    print("\nObserve each test and note FIRST test index that shows cycling.")

    for i in range(total):
        name, cfg, behavior = tests[i]
        _run_case(i + 1, total, name, cfg, behavior)

        if i != total - 1:
            _sleep_seconds_with_countdown(PAUSE_BETWEEN_TESTS_SECONDS)

    print("\nSweep complete.")


def run_single_test(index_1_based):
    tests = build_test_plan()
    idx = int(index_1_based) - 1
    if idx < 0 or idx >= len(tests):
        print("invalid index. valid range: 1..%d" % len(tests))
        return

    name, cfg, behavior = tests[idx]
    _run_case(idx + 1, len(tests), name, cfg, behavior)


def list_tests():
    tests = build_test_plan()
    for i in range(len(tests)):
        name, cfg, behavior = tests[i]
        print("%2d: %s" % (i + 1, name))
        print("    reg: %s" % _fmt_params(cfg))
        print("    beh: %s" % _fmt_params(behavior))


print("hold_cycle_sweep_test loaded")
print("Commands:")
print("  list_tests()")
print("  run_single_test(n)")
print("  run_all_tests()")
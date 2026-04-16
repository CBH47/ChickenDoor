"""
Quick commands to enable/disable testing mode
"""

# To enable testing mode (disable main loop):
# import __main__ as m; m.testing_mode = True; print("Testing mode ON")

# To disable testing mode (re-enable main loop):
# import __main__ as m; m.testing_mode = False; print("Testing mode OFF")

# To check testing mode status:
# import __main__ as m; print("Testing mode:", m.testing_mode)

# To check motor enable state:
# import __main__ as m; print("Motor enable:", m.motor.driver.en.value())

# Quick hold test:
# import __main__ as m; m.motor.hold(); print("Hold engaged")

# Quick stop test:
# import __main__ as m; m.motor.stop(); print("Motor stopped")
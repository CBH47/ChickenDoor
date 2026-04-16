import time

# Set True to force hold sweep on boot.
RUN_HOLD_SWEEP_ON_BOOT = False

if RUN_HOLD_SWEEP_ON_BOOT:
	print("boot.py: starting hold cycle sweep")
	time.sleep(1)
	try:
		import hold_cycle_sweep_test as sweep
		sweep.run_all_tests()
	except Exception as e:
		print("boot.py sweep failed:", e)

	# Keep device idle after sweep so normal app does not start automatically.
	while True:
		time.sleep(1)
else:
	import main

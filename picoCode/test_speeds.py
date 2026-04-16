"""
Simple Motor Speed Testing
Test different stepping speeds to find optimal torque
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


def run_tests():
    print("""
MOTOR SPEED TESTING
===================

The original motor.py has a configurable step_delay_us.
Lower delay = faster stepping = more torque/power

Testing different speeds to see which gives best torque:
""")

    for name, delay_us in configs:
        freq = 1_000_000 / (2 * delay_us)
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"Frequency: {freq:.0f} Hz")
        print(f"{'='*60}")
        
        try:
            # Create motor with this speed, and use the proven configuration
            m = Motor(high_torque=False)
            m.step_delay_us = delay_us
            
            # Run a longer move to catch mid-run torque dropout
            print(f"Running 2000 steps in 5 segments...")
            start = time.ticks_ms()
            for segment in range(5):
                print(f"Segment {segment + 1}/5")
                m.move(1, 400)
                time.sleep_ms(200)
            elapsed = time.ticks_diff(time.ticks_ms(), start)
            
            actual_freq = 2000 * 2000 / elapsed if elapsed > 0 else 0
            print(f"Actual frequency: {actual_freq:.0f} Hz")
            print(f"Completed in {elapsed}ms")
        except Exception as e:
            print(f"Error: {e}")
            import sys
            sys.print_exception(e)
        
        print("Waiting 1 second before next test...")
        time.sleep_ms(1000)
    
    print(f"\n{'='*60}")
    print("TESTING COMPLETE")
    print("="*60)
    print("""
RESULTS:
========
Tell me which speed gave:
1. Most torque (hardest to stall/slow down)?
2. Smoothest operation?
3. Best overall feel?

Then we can make that the default.
""")


if __name__ == '__main__':
    run_tests()


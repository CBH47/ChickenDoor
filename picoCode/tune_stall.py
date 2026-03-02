from motor import Motor
import time

m = Motor()
m.driver.configure()

def test_stall(threshold, steps=1000):
    # Set SGTHRS to threshold and run motor
    m.driver._write_register(0x40, threshold)
    print(f"Testing SGTHRS={threshold}")
    result = m.move(1, steps)
    print(f"Result: {result}")
    time.sleep_ms(500)
    m.move(0, steps)  # return
    return result

print("Stall tuner ready")
print("Run test_stall(value) with values from 0-255")
print("Start low and increase until stall triggers during normal movement")
print("Then back off to 60% of that value")
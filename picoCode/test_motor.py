from motor import Motor

# Create motor with high-torque enabled by default
m = Motor(high_torque=True)

def open_door():
    """Open door with high torque"""
    print(f"EN pin state before: {m.driver.en.value()}")
    result = m.move(1, 5000)
    print(f"EN pin state after: {m.driver.en.value()}")
    print(f"Result: {result}")

def close_door():
    """Close door with high torque"""
    result = m.move(0, 5000)
    print(f"Result: {result}")

def open_door_standard():
    """Open with standard torque for comparison"""
    m_std = Motor(high_torque=False)
    m_std.move(1, 5000)

def increase_step_speed():
    """Test maximum torque with faster stepping"""
    print("Testing maximum aggressive torque (600µs step delay)...")
    m.step_delay_us = 600
    m.move(1, 5000)
    m.step_delay_us = 800  # Reset to default

print("Motor test ready")
print("Commands:")
print("  open_door()          - Open with HIGH torque")
print("  close_door()         - Close with HIGH torque")
print("  open_door_standard() - Open with standard torque (for comparison)")
print("  increase_step_speed()- Test maximum torque")
print(f"\nCurrent torque mode: HIGH-TORQUE")
print(f"Current step delay: {m.step_delay_us}µs")
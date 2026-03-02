from motor import Motor

m = Motor()
m.driver.configure()

def open_door():
    print(f"EN pin state before: {m.driver.en.value()}")
    result = m.move(1, 200)
    print(f"EN pin state after: {m.driver.en.value()}")
    print(f"Result: {result}")

def close_door():
    result = m.move(0, 200)
    print(f"Result: {result}")

print("Motor test ready")
print("Run open_door() or close_door()")
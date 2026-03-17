from machine import Pin
from tmc2209 import TMC2209
import time

driver = TMC2209()
driver.configure()
result = driver._read_register(0x00)
print(f"GCONF: {result}")
time.sleep_ms(500)

en = Pin(4, Pin.OUT)
step = Pin(10, Pin.OUT)
dir = Pin(8, Pin.OUT)

print("Starting raw test...")
en.value(0)
dir.value(1)
time.sleep_ms(5)

for i in range(1600):
    step.value(1)
    time.sleep_us(1000)
    step.value(0)
    time.sleep_us(1000)

en.value(1)
print("Done")
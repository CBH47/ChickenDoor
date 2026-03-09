from machine import Pin
import time

en = Pin(4, Pin.OUT)
step = Pin(6, Pin.OUT)
dir = Pin(3, Pin.OUT)

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
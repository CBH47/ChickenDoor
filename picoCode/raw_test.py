from machine import Pin
import time

en = Pin(4, Pin.OUT)
step = Pin(2, Pin.OUT)
dir = Pin(3, Pin.OUT)

en.value(0)
dir.value(1)
time.sleep_ms(5)

for i in range(400):
    step.value(1)
    time.sleep_us(1000)
    step.value(0)
    time.sleep_us(1000)

en.value(1)
print("Done")
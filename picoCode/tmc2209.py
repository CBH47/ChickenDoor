from machine import Pin, UART
import time

class TMC2209:
    def __init__(self):
        #UartSet
        self.uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
        
        #Sets control pins
        self.step = Pin(2, Pin.OUT)
        self.dir = Pin(3, Pin.OUT)
        self.en = Pin(4,Pin.OUT)

        #Sets diag as input
        self.diag = Pin(18, Pin.IN, Pin.PULL_DOWN)
        
        #Sets initial conditions
        self.en.value(1)
        self.stdby.value(0)
    
    def sleep(self):
        # Put driver into standby - lowest power state
        self.en.value(1)
    
    def enable(self):
        # Enable motor outputs - motor will hold position
        self.en.value(0)
    
    def disable(self):
        # Disable motor outputs - motor spins freely
        self.en.value(1)
    
    def is_stalled(self):
        # Returns True if DIAG pin is high (stall detected)
        return self.diag.value() == 1

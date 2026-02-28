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
    def _calc_crc(self, data):
        # TMC2209 CRC calculation
        crc = 0
        for byte in data:
            for _ in range(8):
                if (crc >> 7) ^ (byte & 0x01):
                    crc = (crc << 1) ^ 0x07
                else:
                    crc = crc << 1
                crc &= 0xFF
                byte >>= 1
        return crc
    def _write_register(self, reg, value):
        # Build 8 byte write packet
        data = [
            0x05,        # sync byte
            0x00,        # slave address
            reg | 0x80,  # register address with write bit set
            (value >> 24) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 8)  & 0xFF,
            (value)       & 0xFF,
        ]
        crc = self._calc_crc(data)
        data.append(crc)
        self.uart.write(bytes(data))
        time.sleep_ms(2)
    def configure(self):
        # GCONF - enable UART control, disable external Vref
        self._write_register(0x00, 0x00000001)
        
        # CHOPCONF - 8 microsteps, standard chopper config
        self._write_register(0x6C, 0x10000053)
        
        # PWMCONF - enable StealthChop
        self._write_register(0x70, 0xC10D0024)
        
        # SGTHRS - StallGuard threshold, start at 10 and tune later
        self._write_register(0x40, 10)
        
        print("TMC2209 configured")

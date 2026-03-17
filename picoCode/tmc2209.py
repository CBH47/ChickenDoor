
from machine import Pin, UART
import time

class TMC2209:
    def __init__(self):
        #UartSet
        self.uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), txbuf=64, rxbuf=64)

        #Sets control pins
        self.step = Pin(10, Pin.OUT)
        self.dir = Pin(8, Pin.OUT)
        self.en = Pin(4,Pin.OUT)

        #Sets diag as input
        self.diag = Pin(14, Pin.IN, Pin.PULL_DOWN)
        
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
        crc = 0
        for byte in data:
            for _ in range(8):
                if (crc >> 7) ^ (byte & 0x01):
                    crc = ((crc << 1) ^ 0x07) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
                byte >>= 1
        return crc
    def _write_register(self, reg, value):
        data = [
            0x05,        
            0x00,        # slave address
            reg | 0x80,
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
        time.sleep_ms(500)

        # Reset driver state by toggling EN
        self.en.value(1)
        time.sleep_ms(200)
        self.en.value(0)
        time.sleep_ms(200)
        self.en.value(1)
        time.sleep_ms(500)
        # GCONF - enable UART control
        self._write_register(0x00, 0x00000001)
        time.sleep_ms(100)
        
        # IHOLD_IRUN - set run current and hold current
        # Bits 8-12 = IRUN (run current 0-31), Bits 0-4 = IHOLD (hold current 0-31)
        # 31 = max current, 16 = ~50%, start at 20 for safety
        self._write_register(0x10, 0x00001614)  # IRUN=22, IHOLD=20
        time.sleep_ms(100)
        
        # CHOPCONF - 8 microsteps
        self._write_register(0x6C, 0x10000053)
        time.sleep_ms(100)
        
        # PWMCONF - enable StealthChop
        self._write_register(0x70, 0xC10D0024)
        time.sleep_ms(100)
        
        # SGTHRS - StallGuard threshold
        self._write_register(0x40, 0)
        time.sleep_ms(100)
        response = self._read_register(0x00)
        print(f"GCONF readback: {response}")
        print("TMC2209 configured")
    def _read_register(self, reg):
        self.uart.read(self.uart.any())
        data = [
            0x05,  # sync byte (was 0x05 - WRONG)
            0x00,  # slave address
            reg,
        ]
        crc = self._calc_crc(data)
        data.append(crc)
        self.uart.write(bytes(data))
        time.sleep_ms(20)
        self.uart.read(4)  # flush echo
        time.sleep_ms(5)
        response = self.uart.read(8)
        return response
    def uart_debug(self):
        # Check how many bytes are in the buffer
        print(f"Bytes in buffer before: {self.uart.any()}")
        self.uart.write(bytes([0x55, 0x00, 0x00, 0xE8]))  # raw GCONF read request
        time.sleep_ms(20)
        print(f"Bytes in buffer after: {self.uart.any()}")
        raw = self.uart.read(self.uart.any())
        print(f"Raw bytes received: {raw}")

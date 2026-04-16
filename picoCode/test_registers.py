"""
TMC2209 Register Experimentation Tool
Safely test different register values to find optimal torque
"""

from machine import Pin, UART
import time
import sys

class TMC2209Experimenter:
    def __init__(self):
        self.uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), txbuf=64, rxbuf=64)
        self.step = Pin(10, Pin.OUT)
        self.dir = Pin(8, Pin.OUT)
        self.en = Pin(4, Pin.OUT)
        self.en.value(1)
    
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
        data = [0x05, 0x00, reg | 0x80]
        data += [(value >> 24) & 0xFF, (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF]
        crc = self._calc_crc(data)
        data.append(crc)
        self.uart.write(bytes(data))
        time.sleep_ms(10)
    
    def _read_register(self, reg):
        self.uart.read(self.uart.any())
        data = [0x05, 0x00, reg]
        crc = self._calc_crc(data)
        data.append(crc)
        self.uart.write(bytes(data))
        time.sleep_ms(5)
        self.uart.read(4)  # echo
        time.sleep_ms(100)
        response = self.uart.read(self.uart.any())
        if response and len(response) >= 8:
            return response[:8]
        return None
    
    def init_driver(self):
        """Standard initialization"""
        time.sleep_ms(500)
        self.en.value(1)
        time.sleep_ms(200)
        self.en.value(0)
        time.sleep_ms(200)
        self.en.value(1)
        time.sleep_ms(500)
        
        # Base config
        self._write_register(0x00, 0x00000004)
        time.sleep_ms(100)
        self._write_register(0x40, 255)  # Max current
        time.sleep_ms(100)
        
        # Enable for communication
        self.en.value(0)
        time.sleep_ms(50)
    
    def test_config(self, name, ihold_irun, chopconf, num_steps=100):
        """Test a specific configuration"""
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"{'='*60}")
        
        self.init_driver()
        
        # Apply test config
        self._write_register(0x10, ihold_irun)
        time.sleep_ms(100)
        self._write_register(0x6C, chopconf)
        time.sleep_ms(100)
        
        # Read back what we set
        resp = self._read_register(0x10)
        if resp:
            val = (resp[3]<<24)|(resp[4]<<16)|(resp[5]<<8)|resp[6]
            print(f"IHOLD_IRUN actual: 0x{val:08X}")
        
        resp = self._read_register(0x6C)
        if resp:
            val = (resp[3]<<24)|(resp[4]<<16)|(resp[5]<<8)|resp[6]
            print(f"CHOPCONF actual: 0x{val:08X}")
            
            # Decode CHOPCONF
            toff = val & 0x0F
            mres = (val >> 12) & 0x0F
            print(f"  → TOFF={toff}, MRES={mres} ({'full stepping' if mres==0 else f'{2**(3+mres)} µsteps'})")
        
        # Run motor
        print(f"Running {num_steps} steps...")
        self.en.value(0)
        self.dir.value(1)
        time.sleep_ms(5)
        
        start = time.ticks_ms()
        for i in range(num_steps):
            self.step.value(1)
            time.sleep_us(1200)
            self.step.value(0)
            time.sleep_us(1200)
        elapsed = time.ticks_diff(time.ticks_ms(), start)
        
        self.en.value(1)
        
        print(f"Completed in {elapsed}ms")
        print(f"Frequency: {num_steps * 2000 / elapsed:.0f} Hz")
        print("→ Now observe motor strength/smoothness")


print("""
ORIGINAL vs CANDIDATE CONFIGURATIONS
=====================================

Original (KNOWN WORKING):
  IHOLD_IRUN: 0x00001F1F (IHOLD=31, IRUN=31)
  CHOPCONF:   0x10000053 (TOFF=3, MRES=1/32µsteps)

Candidates to test:
  1. Full stepping (MRES=0): More torque, very jerky
  2. Higher TOFF (4 or 5): Different chopping frequency
  3. Mid microstepping (MRES=3-5): Balance
""")


def run_tests():
    """Run through different configurations"""
    exp = TMC2209Experimenter()
    
    configs = [
        ("ORIGINAL (baseline)", 0x00001F1F, 0x10000053, 2000),
        ("FULL STEPPING (MRES=0)", 0x00001F1F, 0x10000043, 2000),
        ("Higher TOFF=5", 0x00001F1F, 0x10000055, 2000),
        ("MRES=5 (64 µsteps)", 0x00001F1F, 0x10005053, 2000),
    ]
    
    for name, ihold_irun, chopconf, steps in configs:
        try:
            exp.test_config(name, ihold_irun, chopconf, steps)
            time.sleep_ms(500)
        except Exception as e:
            print(f"Error in {name}: {e}")
            sys.print_exception(e)
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)
    print("""
Observations:
1. Which felt strongest?
2. Which was smoothest?
3. Which had no stalling?

Compare each to the ORIGINAL and report which was best.
""")


if __name__ == "__main__":
    print("Starting systematic register testing...")
    print("Motor will run through all configurations automatically")
    run_tests()

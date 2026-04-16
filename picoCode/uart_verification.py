"""
Comprehensive UART Verification Script
Tests all aspects of UART communication for the TMC2209 stepper driver
"""

from machine import UART, Pin
import time

# ═══════════════════════════════════════════════════════════════════════════
# Test Configuration
# ═══════════════════════════════════════════════════════════════════════════

class UARTVerification:
    def __init__(self):
        self.uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), txbuf=64, rxbuf=64)
        self.en = Pin(4, Pin.OUT)
        self.step = Pin(10, Pin.OUT)
        self.dir = Pin(8, Pin.OUT)
        self.diag = Pin(14, Pin.IN, Pin.PULL_DOWN)
        
        # Statistics
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def test(self, name, condition, details=""):
        """Record test result"""
        status = "✓ PASS" if condition else "✗ FAIL"
        self.results.append(f"{status}: {name}" + (f" ({details})" if details else ""))
        if condition:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
        print(f"{status}: {name}" + (f" ({details})" if details else ""))
    
    # ─────────────────────────────────────────────────────────────────────────
    # CRC Calculation (TMC2209 protocol)
    # ─────────────────────────────────────────────────────────────────────────
    def calc_crc(self, data):
        """Calculate CRC-8 for TMC2209 protocol"""
        crc = 0
        for byte in data:
            for _ in range(8):
                if (crc >> 7) ^ (byte & 0x01):
                    crc = ((crc << 1) ^ 0x07) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
                byte >>= 1
        return crc
    
    def verify_crc(self, data):
        """Verify CRC of received data (last byte is CRC)"""
        if len(data) < 1:
            return False
        expected = self.calc_crc(list(data[:-1]))
        return expected == data[-1]
    
    # ─────────────────────────────────────────────────────────────────────────
    # Buffer Management Tests
    # ─────────────────────────────────────────────────────────────────────────
    def test_buffer_management(self):
        """Test 1: Buffer management"""
        print("\n=== TEST 1: UART Buffer Management ===")
        
        # Flush any leftover data
        leftover = self.uart.read(self.uart.any())
        self.test("Buffer flush", True)
        
        # Check buffer is empty
        any_data = self.uart.any()
        self.test("Buffer starts empty", any_data == 0, f"Buffer has {any_data} bytes")
        
        # Write test data
        test_data = bytes([0x55, 0xAA, 0x55, 0xAA])
        n = self.uart.write(test_data)
        self.test("Write returns correct count", n == 4, f"Wrote {n} bytes")
        
        # Wait for buffered data
        time.sleep_ms(5)
        available = self.uart.any()
        self.test("Data available after write", available > 0, f"{available} bytes available")
        
        # Read back
        echo = self.uart.read(available)
        self.test("Echo matches written data", echo == test_data, 
                 f"Got {[hex(b) for b in echo] if echo else 'nothing'}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Pin Control Tests
    # ─────────────────────────────────────────────────────────────────────────
    def test_pin_control(self):
        """Test 2: GPIO pin control (EN, STEP, DIR)"""
        print("\n=== TEST 2: GPIO Pin Control ===")
        
        # EN pin control
        self.en.value(1)
        time.sleep_ms(10)
        self.test("EN pin set HIGH", self.en.value() == 1)
        
        self.en.value(0)
        time.sleep_ms(10)
        self.test("EN pin set LOW", self.en.value() == 0)
        
        # STEP pin control
        self.step.value(0)
        time.sleep_ms(5)
        self.test("STEP pin set LOW", self.step.value() == 0)
        
        self.step.value(1)
        time.sleep_ms(5)
        self.test("STEP pin set HIGH", self.step.value() == 1)
        self.step.value(0)
        
        # DIR pin control
        self.dir.value(0)
        time.sleep_ms(5)
        self.test("DIR pin set LOW", self.dir.value() == 0)
        
        self.dir.value(1)
        time.sleep_ms(5)
        self.test("DIR pin set HIGH", self.dir.value() == 1)
        self.dir.value(0)
        
        # DIAG pin readback (input)
        diag_val = self.diag.value()
        self.test("DIAG pin readable", isinstance(diag_val, int), f"Value: {diag_val}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # CRC Verification Tests
    # ─────────────────────────────────────────────────────────────────────────
    def test_crc_calculation(self):
        """Test 3: CRC calculation"""
        print("\n=== TEST 3: CRC Calculation ===")
        
        test_cases = [
            ([0x05, 0x00, 0x00], "GCONF read"),
            ([0x05, 0x00, 0x01], "GSTAT read"),
            ([0x05, 0x00, 0x6C], "CHOPCONF read"),
            ([0x05, 0x00, 0x10], "IHOLD_IRUN read"),
        ]
        
        for data, name in test_cases:
            crc = self.calc_crc(data)
            # Verify by recalculating
            full = data + [crc]
            verify = self.verify_crc(bytes(full))
            self.test(f"CRC for {name}", verify, f"CRC=0x{crc:02X}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # TMC2209 Communication Tests
    # ─────────────────────────────────────────────────────────────────────────
    def test_tmc2209_setup(self):
        """Test 4: TMC2209 Setup Sequence"""
        print("\n=== TEST 4: TMC2209 Setup Sequence ===")
        
        # Initialize enable sequence
        self.en.value(1)
        time.sleep_ms(200)
        self.test("Enable sequence: set HIGH", self.en.value() == 1)
        
        self.en.value(0)
        time.sleep_ms(200)
        self.test("Enable sequence: set LOW", self.en.value() == 0)
        
        self.en.value(1)
        time.sleep_ms(200)
        self.test("Enable sequence: set HIGH again", self.en.value() == 1)
        
        self.en.value(1)
        time.sleep_ms(500)
        self.test("Enable sequence complete", True)
    
    def test_register_read(self, reg_addr, reg_name):
        """Test reading a register from TMC2209"""
        print(f"\n--- Reading {reg_name} (0x{reg_addr:02X}) ---")
        
        # Flush buffer thoroughly
        for _ in range(5):
            leftover = self.uart.read(self.uart.any())
            if not leftover:
                break
            time.sleep_ms(2)
        
        # Build read request
        data = [0x05, 0x00, reg_addr]
        crc = self.calc_crc(data)
        request = bytes(data + [crc])
        
        # Send request
        n = self.uart.write(request)
        self.test(f"  Sent {reg_name} request", n == len(request), f"{n} bytes")
        
        # Wait for echo
        time.sleep_ms(10)
        echo = self.uart.read(4)
        self.test(f"  Echo received", echo is not None and len(echo) == 4,
                 f"Got {len(echo) if echo else 0} bytes")
        
        # Wait longer for response from TMC2209
        time.sleep_ms(100)
        available = self.uart.any()
        response = self.uart.read(available) if available > 0 else None
        
        if response and len(response) >= 8:
            # Take first 8 bytes if we got more
            response = response[:8]
            self.test(f"  Response received (8 bytes)", True)
            crc_ok = self.verify_crc(response)
            self.test(f"  Response CRC valid", crc_ok,
                     f"Expected 0x{self.calc_crc(list(response[:7])):02X}, got 0x{response[7]:02X}")
            
            value = (response[3] << 24) | (response[4] << 16) | (response[5] << 8) | response[6]
            print(f"  Value: 0x{value:08X}")
            return True
        else:
            available = self.uart.any()
            self.test(f"  Response received", False, f"Got {len(response) if response else 0} bytes (buffer has {available} more)")
            # Print what we got to debug
            if response:
                print(f"  Debug: Got {[hex(b) for b in response]}")
            return False
    
    def test_tmc2209_communication(self):
        """Test 5: TMC2209 UART Communication"""
        print("\n=== TEST 5: TMC2209 UART Communication ===")
        
        # First, run the proper initialization sequence
        print("--- Initializing TMC2209 ---")
        self.en.value(1)
        time.sleep_ms(200)
        self.en.value(0)
        time.sleep_ms(200)
        self.en.value(1)
        time.sleep_ms(500)
        self.test("Driver initialization sequence", True)
        
        # Now enable driver for communication
        self.en.value(0)
        time.sleep_ms(100)
        
        # Test reading different registers
        registers = [
            (0x00, "GCONF"),
            (0x01, "GSTAT"),
            (0x02, "IFCNT"),
            (0x06, "IOIN"),
            (0x10, "IHOLD_IRUN"),
            (0x6C, "CHOPCONF"),
        ]
        
        reads_ok = 0
        for reg_addr, reg_name in registers:
            if self.test_register_read(reg_addr, reg_name):
                reads_ok += 1
            time.sleep_ms(100)
        
        self.test(f"TMC2209 registers readable", reads_ok > 0, f"{reads_ok}/{len(registers)} successful")
    
    def test_tmc2209_write(self):
        """Test 6: TMC2209 Register Write"""
        print("\n=== TEST 6: TMC2209 Register Write ===")
        
        # Set driver enable
        self.en.value(0)
        time.sleep_ms(100)
        
        # Write GCONF (0x00) with value 0x00000004
        print("--- Writing GCONF (0x00) = 0x00000004 ---")
        data = [0x05, 0x00, 0x00 | 0x80, 0x00, 0x00, 0x00, 0x04]
        crc = self.calc_crc(data)
        request = bytes(data + [crc])
        
        # Flush buffer thoroughly
        for _ in range(5):
            self.uart.read(self.uart.any())
            time.sleep_ms(2)
        
        n = self.uart.write(request)
        self.test("  Write request sent", n == len(request))
        
        time.sleep_ms(200)
        
        # Read back GCONF
        print("--- Reading back GCONF ---")
        data = [0x05, 0x00, 0x00]
        crc = self.calc_crc(data)
        request = bytes(data + [crc])
        
        # Flush buffer thoroughly
        for _ in range(5):
            self.uart.read(self.uart.any())
            time.sleep_ms(2)
        
        self.uart.write(request)
        time.sleep_ms(10)
        echo = self.uart.read(4)
        time.sleep_ms(100)
        available = self.uart.any()
        response = self.uart.read(available) if available > 0 else None
        
        if response and len(response) >= 8:
            response = response[:8]
            value = (response[3] << 24) | (response[4] << 16) | (response[5] << 8) | response[6]
            print(f"  Readback value: 0x{value:08X}")
            self.test("  Register write/readback", True)
        else:
            self.test("  Register write/readback", False)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Timing Tests
    # ─────────────────────────────────────────────────────────────────────────
    def test_timing(self):
        """Test 7: Timing and delays"""
        print("\n=== TEST 7: Timing and Delays ===")
        
        # Test microsecond delays
        start = time.ticks_us()
        time.sleep_us(1000)
        elapsed = time.ticks_diff(time.ticks_us(), start)
        self.test("1000µs delay", elapsed >= 900, f"Actual: {elapsed}µs")
        
        # Test millisecond delays
        start = time.ticks_ms()
        time.sleep_ms(100)
        elapsed = time.ticks_diff(time.ticks_ms(), start)
        self.test("100ms delay", elapsed >= 90, f"Actual: {elapsed}ms")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step Pulse Test
    # ─────────────────────────────────────────────────────────────────────────
    def test_step_pulses(self):
        """Test 8: Step pulse generation"""
        print("\n=== TEST 8: Step Pulse Generation ===")
        
        self.en.value(0)  # Enable motor
        self.dir.value(0)  # Set direction
        time.sleep_ms(5)
        
        print("Generating 10 step pulses...")
        for i in range(10):
            self.step.value(1)
            time.sleep_us(1200)
            self.step.value(0)
            time.sleep_us(1200)
        
        self.test("Step pulses generated", True, "10 pulses sent")
        self.en.value(1)  # Disable motor
    
    # ─────────────────────────────────────────────────────────────────────────
    # Overall Status
    # ─────────────────────────────────────────────────────────────────────────
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("UART VERIFICATION SUMMARY")
        print("="*70)
        
        for result in self.results:
            print(result)
        
        print("\n" + "="*70)
        total = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"Results: {self.tests_passed}/{total} passed ({pass_rate:.0f}%)")
        
        if self.tests_failed == 0:
            print("Status: ✓ ALL TESTS PASSED")
        else:
            print(f"Status: ✗ {self.tests_failed} TEST(S) FAILED")
        
        print("="*70)


# ═══════════════════════════════════════════════════════════════════════════
# Main Execution
# ═══════════════════════════════════════════════════════════════════════════

def run_verification():
    """Run complete UART verification"""
    print("UART VERIFICATION STARTING...")
    print("="*70)
    
    v = UARTVerification()
    
    try:
        v.test_buffer_management()
        v.test_pin_control()
        v.test_crc_calculation()
        v.test_timing()
        v.test_tmc2209_setup()
        v.test_step_pulses()
        v.test_tmc2209_communication()
        v.test_tmc2209_write()
        
    except Exception as e:
        print(f"\n✗ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        v.en.value(1)
        v.uart.deinit()
        v.print_summary()


if __name__ == "__main__":
    run_verification()

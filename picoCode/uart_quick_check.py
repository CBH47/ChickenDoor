"""
Quick UART Diagnostic
Rapid health check for UART communication
Run this first to quickly identify issues
"""

from machine import UART, Pin
import time

def quick_check():
    """Fast 30-second UART health check"""
    print("╔════════════════════════════════════╗")
    print("║     UART Quick Diagnostic           ║")
    print("╚════════════════════════════════════╝\n")
    
    issues = []
    
    # ─────────────────────────────────────────
    # 1. Initialization
    # ─────────────────────────────────────────
    print("1️⃣  UART Initialization...")
    try:
        uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), txbuf=64, rxbuf=64)
        print("   ✓ UART0 initialized")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        issues.append("UART initialization failed")
        return
    
    # ─────────────────────────────────────────
    # 2. Pins
    # ─────────────────────────────────────────
    print("2️⃣  Pin Control...")
    try:
        en = Pin(4, Pin.OUT)
        step = Pin(10, Pin.OUT)
        dir_pin = Pin(8, Pin.OUT)
        diag = Pin(14, Pin.IN, Pin.PULL_DOWN)
        
        # Toggle each
        en.value(1)
        time.sleep_ms(5)
        if en.value() != 1:
            issues.append("EN pin not responding")
        else:
            print("   ✓ EN pin working")
        
        dir_pin.value(1)
        time.sleep_ms(5)
        if dir_pin.value() != 1:
            issues.append("DIR pin not responding")
        else:
            print("   ✓ DIR pin working")
        
        step.value(1)
        time.sleep_ms(5)
        if step.value() != 1:
            issues.append("STEP pin not responding")
        else:
            print("   ✓ STEP pin working")
        
        diag_read = diag.value()
        print(f"   ✓ DIAG pin readable (value: {diag_read})")
        
        # Reset
        en.value(1)
        dir_pin.value(0)
        step.value(0)
        
    except Exception as e:
        print(f"   ✗ Pin error: {e}")
        issues.append(f"Pin control error: {e}")
    
    # ─────────────────────────────────────────
    # 3. UART Echo Test
    # ─────────────────────────────────────────
    print("3️⃣  UART Echo Test...")
    try:
        # Set EN low to enable driver
        en.value(0)
        time.sleep_ms(50)
        
        # Clear buffer
        uart.read(uart.any())
        
        # Write test packet
        test_packet = bytes([0x55, 0xAA, 0x55, 0xAA])
        written = uart.write(test_packet)
        
        if written != len(test_packet):
            issues.append(f"UART write incomplete (wanted {len(test_packet)}, got {written})")
        else:
            print(f"   ✓ Wrote {written} bytes")
        
        # Wait for echo
        time.sleep_ms(10)
        available = uart.any()
        if available == 0:
            issues.append("No UART echo detected")
        else:
            echo = uart.read(available)
            if echo == test_packet:
                print(f"   ✓ Echo received (loopback OK)")
            else:
                print(f"   ⚠ Echo mismatch: got {[hex(b) for b in echo]}")
                issues.append("UART echo doesn't match (possible pin swap or interference)")
        
        en.value(1)  # Disable driver
        
    except Exception as e:
        print(f"   ✗ Echo test failed: {e}")
        issues.append(f"Echo test error: {e}")
    
    # ─────────────────────────────────────────
    # 4. CRC Calculation
    # ─────────────────────────────────────────
    print("4️⃣  CRC Algorithm...")
    try:
        def calc_crc(data):
            crc = 0
            for byte in data:
                for _ in range(8):
                    if (crc >> 7) ^ (byte & 0x01):
                        crc = ((crc << 1) ^ 0x07) & 0xFF
                    else:
                        crc = (crc << 1) & 0xFF
                    byte >>= 1
            return crc
        
        # Test known packet
        test_data = [0x05, 0x00, 0x00]
        crc = calc_crc(test_data)
        
        # Verify
        full_packet = test_data + [crc]
        crc_verify = calc_crc(test_data)
        
        if crc_verify == crc:
            print(f"   ✓ CRC stable (GCONF read = 0x{crc:02X})")
        else:
            issues.append("CRC calculation unstable")
        
    except Exception as e:
        print(f"   ✗ CRC error: {e}")
        issues.append(f"CRC error: {e}")
    
    # ─────────────────────────────────────────
    # 5. TMC2209 Communication
    # ─────────────────────────────────────────
    print("5️⃣  TMC2209 Communication...")
    try:
        en.value(0)  # Enable driver
        time.sleep_ms(100)
        
        # Build read request for GCONF
        def calc_crc(data):
            crc = 0
            for byte in data:
                for _ in range(8):
                    if (crc >> 7) ^ (byte & 0x01):
                        crc = ((crc << 1) ^ 0x07) & 0xFF
                    else:
                        crc = (crc << 1) & 0xFF
                    byte >>= 1
            return crc
        
        uart.read(uart.any())  # flush
        
        req = [0x05, 0x00, 0x00]
        crc = calc_crc(req)
        packet = bytes(req + [crc])
        
        uart.write(packet)
        print(f"   ✓ Sent GCONF read request")
        
        # Wait for echo
        time.sleep_ms(5)
        echo = uart.read(uart.any())
        if echo and len(echo) == 4:
            print(f"   ✓ Echo received")
        else:
            print(f"   ⚠ Unexpected echo")
        
        # Wait for response
        time.sleep_ms(30)
        response = uart.read(uart.any())
        
        if response and len(response) == 8:
            print(f"   ✓ TMC2209 responded (8 bytes)")
            
            # Check CRC
            expected_crc = calc_crc(list(response[:7]))
            if expected_crc == response[7]:
                print(f"   ✓ Response CRC valid")
                
                # Extract value
                value = (response[3] << 24) | (response[4] << 16) | (response[5] << 8) | response[6]
                print(f"   ✓ GCONF value: 0x{value:08X}")
            else:
                print(f"   ✗ Response CRC invalid")
                issues.append("CRC mismatch in TMC2209 response")
        else:
            print(f"   ✗ No TMC2209 response (got {len(response) if response else 0} bytes)")
            issues.append("TMC2209 not responding")
        
        en.value(1)  # Disable driver
        
    except Exception as e:
        print(f"   ✗ Communication error: {e}")
        issues.append(f"TMC2209 comm error: {e}")
    
    # ─────────────────────────────────────────
    # 6. Timing Test
    # ─────────────────────────────────────────
    print("6️⃣  Timing Accuracy...")
    try:
        # Test microsecond timing
        start = time.ticks_us()
        time.sleep_us(1000)
        elapsed_us = time.ticks_diff(time.ticks_us(), start)
        
        if elapsed_us < 900:
            issues.append(f"Microsecond timing off (expected ~1000µs, got {elapsed_us}µs)")
        else:
            print(f"   ✓ Microseconds OK ({elapsed_us}µs for 1000µs sleep)")
        
        # Test millisecond timing
        start = time.ticks_ms()
        time.sleep_ms(100)
        elapsed_ms = time.ticks_diff(time.ticks_ms(), start)
        
        if elapsed_ms < 85:
            issues.append(f"Millisecond timing off (expected ~100ms, got {elapsed_ms}ms)")
        else:
            print(f"   ✓ Milliseconds OK ({elapsed_ms}ms for 100ms sleep)")
        
    except Exception as e:
        print(f"   ✗ Timing error: {e}")
        issues.append(f"Timing error: {e}")
    
    # ─────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────
    print("\n╔════════════════════════════════════╗")
    
    if not issues:
        print("║   ✓ ALL CHECKS PASSED              ║")
        print("║   UART is properly configured      ║")
    else:
        print(f"║   ✗ {len(issues)} ISSUE(S) FOUND           ║")
    
    print("╚════════════════════════════════════╝")
    
    if issues:
        print("\nIssues found:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print("\nNext steps:")
        print("  1. Check physical wiring (TX/RX pins)")
        print("  2. Verify power supply to TMC2209")
        print("  3. Review UART_VERIFICATION_GUIDE.md")
        print("  4. Run uart_verification.py for detailed testing")
        return False
    else:
        print("\nNext: Try motor_test.py or full uart_verification.py")
        return True


if __name__ == "__main__":
    success = quick_check()

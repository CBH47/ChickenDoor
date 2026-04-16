"""
TMC2209 Communication Diagnostic
Helps identify why the driver isn't responding
"""

from machine import UART, Pin
import time

print("╔════════════════════════════════════════════════════════════╗")
print("║         TMC2209 Communication Diagnostic                    ║")
print("╚════════════════════════════════════════════════════════════╝\n")

uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), txbuf=64, rxbuf=64)
en = Pin(4, Pin.OUT)

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

# ───────────────────────────────────────────────────────────────────
# Test 1: Initialization
# ───────────────────────────────────────────────────────────────────
print("TEST 1: Driver Initialization Sequence")
print("-" * 60)

en.value(1)
print(f"Step 1: EN set to 1 (disabled)")
time.sleep_ms(200)

en.value(0)
print(f"Step 2: EN set to 0 (enabled)")
time.sleep_ms(200)

en.value(1)
print(f"Step 3: EN set to 1 (disabled)")
time.sleep_ms(500)

print("✓ Initialization complete - driver should now respond\n")

# ───────────────────────────────────────────────────────────────────
# Test 2: Enable and test response
# ───────────────────────────────────────────────────────────────────
print("TEST 2: Read GCONF Register")
print("-" * 60)

en.value(0)
print("EN set to 0 (driver enabled for communication)")
time.sleep_ms(100)

# Clear buffer
uart.read(uart.any())
print("Buffer cleared")

# Send GCONF read request
req_data = [0x05, 0x00, 0x00]
crc = calc_crc(req_data)
request = bytes(req_data + [crc])

print(f"\nSending GCONF read request: {[hex(b) for b in request]}")
written = uart.write(request)
print(f"  → Wrote {written} bytes")

# Wait and read echo
print(f"\nWaiting 10ms for echo...")
time.sleep_ms(10)
avail_before_echo = uart.any()
print(f"  → Bytes available: {avail_before_echo}")

if avail_before_echo > 0:
    echo = uart.read(avail_before_echo)
    print(f"  → Echo: {[hex(b) for b in echo]}")
    
    if echo == request:
        print(f"  ✓ Echo matches request (UART loopback working)")
    else:
        print(f"  ⚠ Echo doesn't match (data corruption?)")
else:
    print(f"  ✗ No echo received")

# Wait for response
print(f"\nWaiting 150ms for TMC2209 response...")
time.sleep_ms(150)

avail = uart.any()
print(f"  → Bytes available in buffer: {avail}")

if avail > 0:
    response = uart.read(avail)
    print(f"  → Raw data: {[hex(b) for b in response]}")
    print(f"  → Hex: {' '.join([f'{b:02X}' for b in response])}")
    
    if len(response) >= 8:
        print(f"\n  ✓ Received {len(response)} bytes (enough for response)")
        
        # Parse first 8 bytes
        first_8 = response[:8]
        print(f"\n  First 8 bytes:")
        print(f"    Sync:   0x{first_8[0]:02X} (expect 0x05)")
        print(f"    Addr:   0x{first_8[1]:02X} (expect 0x00)")
        print(f"    Reg:    0x{first_8[2]:02X} (expect 0x00)")
        print(f"    Val[3]: 0x{first_8[3]:02X}")
        print(f"    Val[2]: 0x{first_8[4]:02X}")
        print(f"    Val[1]: 0x{first_8[5]:02X}")
        print(f"    Val[0]: 0x{first_8[6]:02X}")
        print(f"    CRC:    0x{first_8[7]:02X}")
        
        # Check CRC
        expected_crc = calc_crc(list(first_8[:7]))
        print(f"\n  CRC Check: expected=0x{expected_crc:02X}, got=0x{first_8[7]:02X}")
        if expected_crc == first_8[7]:
            print(f"  ✓ CRC is VALID")
            
            # Extract value
            value = (first_8[3] << 24) | (first_8[4] << 16) | (first_8[5] << 8) | first_8[6]
            print(f"\n  ✓ GCONF Value: 0x{value:08X}")
            print(f"  ✓✓✓ SUCCESS - TMC2209 is responding correctly!")
        else:
            print(f"  ✗ CRC MISMATCH")
    else:
        print(f"  ✗ Response too short ({len(response)} bytes, need 8)")
else:
    print(f"  ✗ NO RESPONSE from TMC2209")
    print(f"  \n  → Buffer still empty after 150ms delay")

# ───────────────────────────────────────────────────────────────────
# Test 3: Try different addresses
# ───────────────────────────────────────────────────────────────────
print(f"\n\nTEST 3: Try Different Node Addresses")
print("-" * 60)

for addr in range(4):
    uart.read(uart.any())  # clear
    
    req_data = [0x05, addr, 0x00]
    crc = calc_crc(req_data)
    request = bytes(req_data + [crc])
    
    print(f"Address {addr}: Sending {[hex(b) for b in request]}")
    uart.write(request)
    
    time.sleep_ms(10)
    uart.read(4)  # discard echo
    
    time.sleep_ms(100)
    avail = uart.any()
    
    if avail > 0:
        response = uart.read(avail)
        print(f"  ✓ Got {len(response)} bytes: {[hex(b) for b in response]}")
    else:
        print(f"  ✗ No response")

# ───────────────────────────────────────────────────────────────────
# Test 4: Try with shorter waits
# ───────────────────────────────────────────────────────────────────
print(f"\n\nTEST 4: Try Different Wait Times")
print("-" * 60)

wait_times = [10, 20, 50, 100, 200, 500]

for wait_ms in wait_times:
    uart.read(uart.any())  # clear
    
    req_data = [0x05, 0x00, 0x00]
    crc = calc_crc(req_data)
    request = bytes(req_data + [crc])
    
    uart.write(request)
    time.sleep_ms(5)
    uart.read(4)  # discard echo
    
    time.sleep_ms(wait_ms)
    avail = uart.any()
    
    status = "✓" if avail > 0 else "✗"
    print(f"  Wait {wait_ms:3d}ms: {status} {avail} bytes available")

# ───────────────────────────────────────────────────────────────────
# Summary
# ───────────────────────────────────────────────────────────────────
print(f"\n\n" + "=" * 60)
print("DIAGNOSTIC SUGGESTIONS:")
print("=" * 60)
print("""
If NO RESPONSE detected:
  1. Check RX/TX pin connections between Pico and TMC2209
  2. Check power supply to TMC2209 (typically 5V or 12V)
  3. Check GND connection between Pico and TMC2209
  4. Verify baud rate (should be 115200)
  5. Try connecting RX to TX and TX to RX (swap them)

If CRC MISMATCH:
  1. Verify CRC algorithm matches TMC2209 spec
  2. Check for data corruption on the line
  3. Try lower baud rate if available

If SUCCESS:
  1. Run full uart_verification.py to test all functionality
""")

en.value(1)  # disable
uart.deinit()
print("Diagnostic complete - driver disabled")

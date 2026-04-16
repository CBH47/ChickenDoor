# UART Verification Guide

## Overview
This guide documents how to verify UART communication on your Pico board with the TMC2209 stepper motor driver.

## UART Configuration
- **Controller**: RP2040 (Pico) UART0
- **Baud Rate**: 115200
- **TX Pin**: GPIO 16
- **RX Pin**: GPIO 17
- **Buffer Sizes**: TX=64, RX=64
- **Protocol**: TMC2209 UART interface with CRC-8 checksums

## Test Files

### 1. `uart_verification.py` (Comprehensive)
A complete verification suite that tests:
- **Buffer Management**: UART TX/RX buffering
- **Pin Control**: EN, STEP, DIR, DIAG pins
- **CRC Calculation**: TMC2209 checksum validation
- **Timing**: Microsecond and millisecond accuracy
- **TMC2209 Setup**: Proper initialization sequence
- **Register Read**: GCONF, GSTAT, IFCNT, IOIN, IHOLD_IRUN, CHOPCONF
- **Register Write**: Write and readback verification
- **Step Pulses**: Motor control signal generation

**Usage**:
```python
from uart_verification import run_verification
run_verification()
```

### 2. `uartTest.py` (TMC2209 Focused)
Focused testing of TMC2209 communication including:
- CRC verification for all test registers
- Individual register reads
- Echo verification
- Node address scanning (addresses 0-3)

**Usage**:
```python
import uartTest
```

### 3. `test_motor.py` (Motor Integration)
High-level motor control testing:
```python
from test_motor import m
m.driver.configure()
open_door()   # Move 200 steps in direction 1
close_door()  # Move 200 steps in direction 0
```

### 4. `raw_test.py` (Low-level)
Direct GPIO and UART control for debugging

## Common UART Issues and Solutions

### Issue 1: No Response from TMC2209
**Possible Causes**:
- Driver not enabled (EN pin high when should be low)
- Incorrect UART pins or baud rate
- Bad UART connection/wiring
- Incorrect CRC calculation

**Debug Steps**:
```python
# Check pins
en = Pin(4, Pin.OUT)
print(f"EN pin state: {en.value()}")  # Should be 0 for enabled

# Check buffer
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), txbuf=64, rxbuf=64)
print(f"Bytes available: {uart.any()}")  # Check for leftover data
```

### Issue 2: Echo Mismatch
**Possible Causes**:
- TX and RX pins swapped
- UART loopback not working
- Timing issues (reading echo too quickly)

**Solution**:
```python
# Write test data
uart.write(bytes([0x55, 0xAA]))
time.sleep_ms(5)  # Wait for echo
echo = uart.read(uart.any())
print(f"Echo: {echo}")  # Should be [0x55, 0xAA]
```

### Issue 3: CRC Errors
**Possible Causes**:
- Incorrect CRC calculation
- Corrupted serial data
- Baud rate mismatch

**Verification**:
```python
from uart_verification import UARTVerification
v = UARTVerification()

# Test known CRC
crc = v.calc_crc([0x05, 0x00, 0x00])
print(f"GCONF read CRC: 0x{crc:02X}")  # Should be consistent

# Verify full packet
full_packet = bytes([0x05, 0x00, 0x00, crc])
print(f"CRC valid: {v.verify_crc(full_packet)}")  # Should be True
```

### Issue 4: Register Reads Return Garbage
**Possible Causes**:
- TMC2209 not in correct state
- Need to read echo before response
- Buffer not flushed before read

**Correct Sequence**:
```python
# Flush any leftover data
uart.read(uart.any())

# Send request
uart.write(request_packet)

# Wait and read echo (reflected TX)
time.sleep_ms(5)
echo = uart.read(4)

# Wait for response from chip
time.sleep_ms(30)
response = uart.read(8)

# Verify response
if response and len(response) == 8:
    print(f"Valid response received")
```

## Pin Reference

| Pin | GPIO | Function | Direction | Notes |
|-----|------|----------|-----------|-------|
| TX  | 16   | UART TX  | Out       | To TMC2209 RX |
| RX  | 17   | UART RX  | In        | From TMC2209 TX |
| EN  | 4    | Enable   | Out       | Low = enabled |
| DIR | 8    | Direction| Out       | 0 = one direction, 1 = other |
| STEP| 10   | Step     | Out       | Pulse to step motor |
| DIAG| 14   | Diagnostic| In       | High = stall detected (with internal pull-down) |

## TMC2209 Register Addresses

| Name | Address | Use |
|------|---------|-----|
| GCONF | 0x00 | General configuration |
| GSTAT | 0x01 | General status flags |
| IFCNT | 0x02 | Interface character counter |
| IOIN | 0x06 | Input/output pins |
| IHOLD_IRUN | 0x10 | Hold and run current settings |
| CHOPCONF | 0x6C | Chopper config |

## UART Protocol Details

### Register Read Packet (4 bytes + CRC)
```
Byte 0: 0x05        (Sync byte)
Byte 1: 0x00        (Slave address)
Byte 2: REG_ADDR    (Register to read)
Byte 3: CRC8        (Checksum, calculated on bytes 0-2)
```

### Register Write Packet (8 bytes + CRC)
```
Byte 0: 0x05        (Sync byte)
Byte 1: 0x00        (Slave address)
Byte 2: REG_ADDR | 0x80  (Register to write, bit 7 set)
Byte 3-6: VALUE     (32-bit value, MSB first)
Byte 7: CRC8        (Checksum, calculated on bytes 0-6)
```

### Response Packet (8 bytes)
```
Byte 0: 0x05        (Sync echo)
Byte 1: 0x00        (Address echo)
Byte 2: REG_ADDR    (Register address)
Byte 3-6: VALUE     (32-bit value read, MSB first)
Byte 7: CRC8        (Response checksum)
```

## Timing Requirements

| Operation | Min Delay |
|-----------|-----------|
| After EN sequence | 500ms |
| After register write | 100ms |
| Between UART writes | 50ms |
| Read echo wait | 5ms |
| Read response wait | 30ms |
| STEP pulse width | 600µs |

## Expected Behavior

### Normal Configuration Sequence
1. UART initialized at 115200 baud
2. EN pin cycled: HIGH → LOW → HIGH (with delays)
3. Register writes to configure driver
4. Register reads to verify configuration
5. Motor controlled via STEP/DIR pulses

### Motor Movement
1. EN pin set LOW (enables motor)
2. DIR pin set to desired direction
3. STEP pulses generated (pulse width 600µs recommended)
4. EN pin set HIGH (disables motor)

## Troubleshooting Checklist

- [ ] UART initialization succeeds (no exceptions)
- [ ] EN pin responds to writes (0/1 toggle works)
- [ ] STEP pin generates clean pulses (can trace on scope if available)
- [ ] DIR pin controllable (0/1 toggle works)
- [ ] CRC calculations consistent and repeatable
- [ ] Echo received after each UART write
- [ ] TMC2209 responds to read requests
- [ ] Response CRCs validate correctly
- [ ] Register values stable across reads
- [ ] Motor responds to STEP signals
- [ ] Buffer management works (no overflow/corruption)

## Running the Verification

On your Pico, in the REPL:

```python
# Quick test - just run uartTest.py
import uartTest

# Comprehensive test - run full verification
from uart_verification import run_verification
run_verification()

# Motor test
from test_motor import m
m.driver.configure()
open_door()
close_door()
```

## Next Steps if Issues Found

1. **No response at all**: Check physical wiring and baud rate
2. **Intermittent responses**: Increase delays or check power supply
3. **CRC errors**: Verify CRC algorithm matches TMC2209 spec
4. **Motor doesn't move**: Verify DIR/STEP pin control and EN state
5. **Stall detection issues**: Check DIAG pin connection and pull-down

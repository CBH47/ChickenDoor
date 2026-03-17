from machine import UART, Pin
import time

print("=== TMC2209 Comprehensive UART Test ===")
print()

# ── Setup ─────────────────────────────────────────────
print("--- Setup ---")
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), txbuf=64, rxbuf=64)
en = Pin(4, Pin.OUT)
en.value(0)
print("UART initialized on GP16/GP17")
print("EN set LOW (driver enabled)")
time.sleep_ms(200)
print()

# ── CRC Function ──────────────────────────────────────
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

# ── Verify CRCs ───────────────────────────────────────
print("--- CRC Verification ---")
regs = {
    "GCONF    (0x00)": 0x00,
    "GSTAT    (0x01)": 0x01,
    "IFCNT    (0x02)": 0x02,
    "IOIN     (0x06)": 0x06,
    "CHOPCONF (0x6C)": 0x6C,
}
requests = {}
for name, reg in regs.items():
    packet = [0x05, 0x00, reg]
    crc = calc_crc(packet)
    full = bytes(packet + [crc])
    requests[name] = full
    print(f"  {name}: {[hex(b) for b in full]}")
print()

# ── Flush buffer ──────────────────────────────────────
def flush(label=""):
    leftover = uart.read(uart.any())
    if leftover:
        print(f"  Flushed{' (' + label + ')' if label else ''}: {leftover}")

# ── Single read attempt ───────────────────────────────
def read_register(name, packet, node=0x00):
    print(f"--- Reading {name} ---")
    flush("before write")
    
    n = uart.write(packet)
    print(f"  Wrote {n} bytes: {[hex(b) for b in packet]}")
    
    time.sleep_ms(5)
    echo = uart.read(4)
    print(f"  Echo (our TX):     {echo}")
    if echo and echo == packet:
        print(f"  Echo match: OK")
    elif echo:
        print(f"  Echo MISMATCH - got {[hex(b) for b in echo]}")
    else:
        print(f"  No echo received")
    
    time.sleep_ms(30)
    reply = uart.read(8)
    print(f"  TMC2209 reply:     {reply}")
    
    if reply and len(reply) == 8:
        print(f"  Reply bytes:  {[hex(b) for b in reply]}")
        expected_crc = calc_crc(list(reply[:7]))
        print(f"  Reply CRC:    expected=0x{expected_crc:02X} got=0x{reply[7]:02X}")
        if expected_crc == reply[7]:
            print(f"  CRC OK")
            value = (reply[3] << 24) | (reply[4] << 16) | (reply[5] << 8) | reply[6]
            print(f"  Value: 0x{value:08X} ({value})")
        else:
            print(f"  CRC MISMATCH")
    elif reply:
        print(f"  Short reply: only {len(reply)} bytes")
    else:
        print(f"  No reply from TMC2209")
    print()

# ── Test all registers ────────────────────────────────
print("--- Register Reads ---")
for name, packet in requests.items():
    read_register(name, packet)
    time.sleep_ms(50)

# ── Try all node addresses ────────────────────────────
print("--- Node Address Scan ---")
for addr in range(4):
    packet = bytes([0x05, addr, 0x00, calc_crc([0x05, addr, 0x00])])
    print(f"  Node {addr}: sending {[hex(b) for b in packet]}")
    flush()
    uart.write(packet)
    time.sleep_ms(5)
    uart.read(4)  # discard echo
    time.sleep_ms(30)
    reply = uart.read(8)
    print(f"  Node {addr}: reply = {reply}")
    time.sleep_ms(50)

print()
print("=== Test Complete ===")
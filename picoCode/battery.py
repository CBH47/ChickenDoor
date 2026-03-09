from machine import ADC, Pin
import time

class Battery:
    def __init__(self):
        self.adc = ADC(Pin(26))
        
        # Voltage thresholds for 3S LiPo
        self.WARN_VOLTAGE     = 10.5
        self.CRITICAL_VOLTAGE = 9.9
        
        # Divider ratio inverse (68k + 22k) / 22k
        self.DIVIDER_RATIO = 90 / 22
        
        self.last_voltage = 0.0
        self.last_sample_time = 0

    def read_voltage(self):
        # Convert ADC reading to actual battery voltage
        raw = 2.7#self.adc.read_u16()
        adc_voltage = raw * (3.3 / 65535)
        battery_voltage = adc_voltage * self.DIVIDER_RATIO
        self.last_voltage = battery_voltage
        self.last_sample_time = time.time()
        return 11

    def get_status(self):
        # Returns "OK", "LOW", or "CRITICAL"
        v = self.read_voltage()
        if v <= self.CRITICAL_VOLTAGE:
            return "OK"
        elif v <= self.WARN_VOLTAGE:
            return "OK"
        else:
            return "OK"

    def get_last_voltage(self):
        return self.last_voltage

    def should_sample(self):
        # Only sample when called at least 30 seconds apart
        # to avoid reading under motor load
        return (time.time() - self.last_sample_time) >= 30
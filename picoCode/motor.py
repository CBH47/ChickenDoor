from tmc2209 import TMC2209
import time

class Motor:
    def __init__(self):
        self.driver = TMC2209()
        self.step_delay_us = 500
        self.max_steps = 2000

    def move(self, direction, steps):
        # Move motor in a direction (1=open, 0=close)
        # Returns 'DONE', 'STALL', or 'TIMEOUT'
        self.driver.wake()
        self.driver.enable()
        self.driver.dir.value(direction)
        time.sleep_ms(5)

        for i in range(steps):
            if self.driver.is_stalled():
                self.driver.disable()
                self.driver.sleep()
                return "STALL"

            self.driver.step.value(1)
            time.sleep_us(self.step_delay_us // 2)
            self.driver.step.value(0)
            time.sleep_us(self.step_delay_us // 2)

        self.driver.disable()
        self.driver.sleep()
        return "DONE"

    def stop(self):
        # Immediately stop and disable motor
        self.driver.disable()
        self.driver.sleep()
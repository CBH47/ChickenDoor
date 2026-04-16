from tmc2209 import TMC2209
import time

class Motor:
    # State constants
    IDLE    = "IDLE"
    MOVING  = "MOVING"

    def __init__(self, high_torque=False):
        self.driver = TMC2209()
        # Slightly slower stepping gives the motor a bit more effective torque.
        self.step_delay_us = 340
        self.max_steps = 4800
        self.close_steps = 2000

        self._state = Motor.IDLE

        if high_torque:
            self.driver.configure_high_torque()
        else:
            self.driver.configure()

    # ------------------------------------------------------------------ #
    # Internal                                                            #
    # ------------------------------------------------------------------ #

    def _pulse_step(self):
        self.driver.step.value(1)
        time.sleep_us(self.step_delay_us)
        self.driver.step.value(0)
        time.sleep_us(self.step_delay_us)

    # ------------------------------------------------------------------ #
    # Public API                                                          #
    # ------------------------------------------------------------------ #

    def move(self, direction, steps):
        """Run the motor and leave it IDLE (de-energised) when done."""
        self._state = Motor.MOVING

        self.driver.enable()
        self.driver.dir.value(direction)
        time.sleep_ms(5)
        print(f"Moving: dir={direction} steps={steps}")

        for i in range(steps):
            if i % 100 == 0:
                print(f"Step {i}")
            self._pulse_step()

        self._state = Motor.IDLE
        print("Move complete")
        return "DONE"

    def release(self):
        """De-energise the motor."""
        self._state = Motor.IDLE
        self.driver.disable()
        print("Motor released")

    def stop(self):
        self.release()

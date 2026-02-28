class StateMachine:
    def __init__(self):
        self.state = "IDLE"
        self.valid_states = [
            "IDLE",
            "OPENING",
            "CLOSING",
            "OPEN",
            "CLOSED",
            "STALLED",
            "LOW_BATTERY",
            "BATTERY_CRITICAL"
        ]

    def transition(self, new_state):
        # Only transition if the new state is valid
        if new_state in self.valid_states:
            print(f"State: {self.state} -> {new_state}")
            self.state = new_state
            return True
        print(f"Invalid state: {new_state}")
        return False

    def is_busy(self):
        # Returns True if a move is in progress
        return self.state in ["OPENING", "CLOSING"]

    def can_accept_command(self):
        # Returns True if the state machine can accept a new command
        return self.state not in ["OPENING", "CLOSING", "BATTERY_CRITICAL"]

    def get_state(self):
        return self.state
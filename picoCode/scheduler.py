import json
import os
import time

class Scheduler:
    def __init__(self):
        print("Scheduler init...")
        self.rules = []
        self.schedule_file = "schedule.json"
        self.last_checked_minute = -1
        self.load()
        print("Scheduler done")

    def load(self):
        # Load rules from flash storage if file exists
        try:
            if "schedule.json" in os.listdir():
                with open(self.schedule_file, "r") as f:
                    self.rules = json.load(f)
                print(f"Loaded {len(self.rules)} schedule rules")
            else:
                print("No schedule file found, starting empty")
        except Exception as e:
            print(f"Failed to load schedule: {e}")
            self.rules = []

    def save(self):
        # Save rules to flash storage
        try:
            with open(self.schedule_file, "w") as f:
                json.dump(self.rules, f)
            print("Schedule saved")
            return True
        except Exception as e:
            print(f"Failed to save schedule: {e}")
            return False

    def add_rule(self, hour, minute, days, action):
        # days is a list e.g. ["Mon","Tue","Wed","Thu","Fri"]
        # action is "OPEN" or "CLOSE"
        rule = {
            "hour": hour,
            "minute": minute,
            "days": days,
            "action": action
        }
        self.rules.append(rule)
        self.save()

    def remove_rule(self, index):
        # Remove a rule by its index in the list
        if 0 <= index < len(self.rules):
            self.rules.pop(index)
            self.save()
            return True
        return False

    def get_rules(self):
        return self.rules

    def check(self):
        # Call this in the main loop
        # Returns an action string "OPEN"/"CLOSE" or None
        now = time.localtime()
        current_hour   = now[3]
        current_minute = now[4]
        current_day    = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][now[6]]

        # Only check once per minute
        if current_minute == self.last_checked_minute:
            return None
        self.last_checked_minute = current_minute

        for rule in self.rules:
            if (rule["hour"] == current_hour and
                rule["minute"] == current_minute and
                current_day in rule["days"]):
                print(f"Scheduler firing: {rule['action']}")
                return rule["action"]

        return None
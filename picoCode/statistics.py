import json
import os
import time

class Statistics:
    def __init__(self):
        print("Statistics init...")
        self.stats_file = "stats.json"
        self.daily_stats = {}
        self.total_operations = 0
        self.load()
        print("Statistics done")

    def load(self):
        # Load statistics from flash storage
        try:
            if self.stats_file in os.listdir():
                with open(self.stats_file, "r") as f:
                    data = json.load(f)
                    self.daily_stats = data.get("daily", {})
                    self.total_operations = data.get("total", 0)
                print(f"Loaded stats: {self.total_operations} total operations")
            else:
                print("No stats file found, starting fresh")
                self._initialize_stats()
        except Exception as e:
            print(f"Failed to load stats: {e}")
            self._initialize_stats()

    def _initialize_stats(self):
        # Initialize with empty stats for current week
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.daily_stats = {day: 0 for day in days}
        self.total_operations = 0

    def save(self):
        # Save statistics to flash storage
        try:
            data = {
                "daily": self.daily_stats,
                "total": self.total_operations,
                "last_updated": time.time()
            }
            with open(self.stats_file, "w") as f:
                json.dump(data, f)
            print("Statistics saved")
            return True
        except Exception as e:
            print(f"Failed to save stats: {e}")
            return False

    def record_operation(self, operation_type):
        # Record a door operation (OPEN or CLOSE)
        try:
            # Get current day of week
            now = time.localtime()
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            current_day = day_names[now[6]]

            # Increment daily count
            if current_day not in self.daily_stats:
                self.daily_stats[current_day] = 0
            self.daily_stats[current_day] += 1

            # Increment total
            self.total_operations += 1

            # Save periodically (every 10 operations or daily rollover)
            if self.total_operations % 10 == 0:
                self.save()

            print(f"Recorded {operation_type} operation. Day: {current_day}, Total: {self.total_operations}")

        except Exception as e:
            print(f"Failed to record operation: {e}")

    def get_daily_stats(self):
        # Return daily statistics as dict
        return self.daily_stats

    def get_total_operations(self):
        # Return total operation count
        return self.total_operations

    def get_stats_summary(self):
        # Return comprehensive stats summary
        total_week = sum(self.daily_stats.values())
        avg_daily = total_week / len(self.daily_stats) if self.daily_stats else 0

        return {
            "daily": self.daily_stats,
            "total": self.total_operations,
            "weekly_total": total_week,
            "daily_average": round(avg_daily, 1),
            "last_updated": time.time()
        }

    def reset_stats(self):
        # Reset all statistics
        self._initialize_stats()
        self.save()
        print("Statistics reset")
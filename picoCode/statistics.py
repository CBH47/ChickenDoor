import json
import os
import time

class Statistics:
    def __init__(self):
        print("Statistics init...")
        self.stats_file = "stats.json"
        self.daily_stats = {}
        self.recent_activity = []
        self.total_operations = 0
        self.last_updated = 0
        self.current_week_key = None
        self.load()
        print("Statistics done")

    def load(self):
        # Load statistics from flash storage
        try:
            if self.stats_file in os.listdir():
                with open(self.stats_file, "r") as f:
                    data = json.load(f)
                    self.daily_stats = self._normalize_daily_stats(data.get("daily", {}))
                    self.recent_activity = self._normalize_recent_activity(data.get("recent_activity", []))
                    self.total_operations = int(data.get("total", 0))
                    self.last_updated = data.get("last_updated", 0)
                    self.current_week_key = data.get("week_key")

                self._ensure_current_week()
                print(f"Loaded stats: {self.total_operations} total operations")
            else:
                print("No stats file found, starting fresh")
                self._initialize_stats()
                self.save()
        except Exception as e:
            print(f"Failed to load stats: {e}")
            self._initialize_stats()
            self.save()

    def _normalize_daily_stats(self, daily):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return {day: int(daily.get(day, 0)) for day in days}

    def _week_key(self, tm):
        year = tm[0]
        weekday = tm[6]
        day_of_year = tm[7] if len(tm) > 7 else 0
        week_start = day_of_year - weekday
        return f"{year}-{week_start}"

    def _normalize_recent_activity(self, entries):
        normalized = []
        if not isinstance(entries, list):
            return normalized

        for item in entries:
            if not isinstance(item, dict):
                continue
            action = str(item.get("action", "")).upper()
            reason = str(item.get("reason", "Unknown"))
            timestamp = int(item.get("timestamp", 0) or 0)
            if action in ("OPEN", "CLOSE"):
                normalized.append({
                    "timestamp": timestamp,
                    "action": action,
                    "reason": reason,
                })

        normalized.sort(key=lambda e: e.get("timestamp", 0), reverse=True)
        return normalized[:5]

    def _ensure_current_week(self):
        now = time.localtime()
        current_key = self._week_key(now)
        if self.current_week_key != current_key:
            self.daily_stats = {day: 0 for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
            self.current_week_key = current_key
            self.last_updated = time.time()
            self.save()

    def _initialize_stats(self):
        # Initialize with empty stats for current week
        self.daily_stats = {day: 0 for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
        self.recent_activity = []
        self.total_operations = 0
        self.last_updated = time.time()
        self.current_week_key = self._week_key(time.localtime())

    def save(self):
        # Save statistics to flash storage
        try:
            data = {
                "daily": self.daily_stats,
                "recent_activity": self.recent_activity,
                "total": self.total_operations,
                "last_updated": self.last_updated,
                "week_key": self.current_week_key,
            }
            with open(self.stats_file, "w") as f:
                json.dump(data, f)
            print("Statistics saved")
            return True
        except Exception as e:
            print(f"Failed to save stats: {e}")
            return False

    def record_operation(self, operation_type, reason="Manual"):
        # Record a door operation (OPEN or CLOSE)
        try:
            now = time.localtime()
            self._ensure_current_week()
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            current_day = day_names[now[6]]

            self.daily_stats[current_day] = self.daily_stats.get(current_day, 0) + 1
            self.total_operations += 1
            self.last_updated = time.time()

            self.recent_activity.insert(0, {
                "timestamp": int(self.last_updated),
                "action": str(operation_type).upper(),
                "reason": str(reason),
            })
            self.recent_activity = self.recent_activity[:5]

            if not self.save():
                print("Warning: statistics save failed after operation")

            print(f"Recorded {operation_type} operation ({reason}). Day: {current_day}, Total: {self.total_operations}")
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
            "recent_activity": self.recent_activity,
            "total": self.total_operations,
            "weekly_total": total_week,
            "daily_average": round(avg_daily, 1),
            "last_updated": self.last_updated,
        }

    def reset_stats(self):
        # Reset all statistics
        self._initialize_stats()
        self.save()
        print("Statistics reset")
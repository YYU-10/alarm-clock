import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alarms.json")


@dataclass
class Alarm:
    hour: int
    minute: int
    note: str = ""
    enabled: bool = True
    ringtone: str = ""
    repeat_days: List[int] = field(default_factory=list)  # 0=周一 ... 6=周日, 空=仅一次
    alarm_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    snoozed_until: Optional[str] = None  # ISO格式时间字符串

    def time_str(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"

    def repeat_str(self) -> str:
        if not self.repeat_days:
            return "仅一次"
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        if self.repeat_days == list(range(7)):
            return "每天"
        if self.repeat_days == list(range(5)):
            return "工作日"
        if self.repeat_days == [5, 6]:
            return "周末"
        return "、".join(day_names[d] for d in sorted(self.repeat_days))


class AlarmStore:
    def __init__(self):
        self.alarms: List[Alarm] = []
        self.load()

    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.alarms = []
                for item in data:
                    item.pop("snoozed_until", None)
                    self.alarms.append(Alarm(**item))
            except (json.JSONDecodeError, TypeError):
                self.alarms = []
        else:
            self.alarms = []

    def save(self):
        data = []
        for alarm in self.alarms:
            d = asdict(alarm)
            d.pop("snoozed_until", None)
            data.append(d)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, alarm: Alarm):
        self.alarms.append(alarm)
        self.save()

    def remove(self, alarm_id: str):
        self.alarms = [a for a in self.alarms if a.alarm_id != alarm_id]
        self.save()

    def toggle(self, alarm_id: str):
        for alarm in self.alarms:
            if alarm.alarm_id == alarm_id:
                alarm.enabled = not alarm.enabled
                break
        self.save()

    def update(self, alarm: Alarm):
        for i, a in enumerate(self.alarms):
            if a.alarm_id == alarm.alarm_id:
                self.alarms[i] = alarm
                break
        self.save()

    def get(self, alarm_id: str) -> Optional[Alarm]:
        for alarm in self.alarms:
            if alarm.alarm_id == alarm_id:
                return alarm
        return None

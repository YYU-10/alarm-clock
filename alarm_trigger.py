from datetime import datetime, timedelta
from typing import List

from alarm_model import Alarm, AlarmStore


class AlarmTrigger:
    def __init__(self, store: AlarmStore):
        self.store = store
        self._triggered_this_minute: set = set()
        self._last_minute: int = -1

    def check(self, now: datetime) -> List[Alarm]:
        current_minute = now.hour * 60 + now.minute
        if current_minute != self._last_minute:
            self._triggered_this_minute.clear()
            self._last_minute = current_minute

        triggered = []
        for alarm in self.store.alarms:
            if not alarm.enabled:
                continue
            if alarm.alarm_id in self._triggered_this_minute:
                continue

            # 检查延后提醒
            if alarm.snoozed_until:
                snooze_time = datetime.fromisoformat(alarm.snoozed_until)
                if now < snooze_time:
                    continue
                alarm.snoozed_until = None

            if alarm.hour == now.hour and alarm.minute == now.minute:
                # 检查重复周期
                if alarm.repeat_days:
                    weekday = now.weekday()  # 0=周一
                    if weekday not in alarm.repeat_days:
                        continue
                triggered.append(alarm)
                self._triggered_this_minute.add(alarm.alarm_id)

        return triggered

    def snooze(self, alarm: Alarm, minutes: int = 5):
        alarm.snoozed_until = (datetime.now() + timedelta(minutes=minutes)).isoformat()

    def dismiss(self, alarm: Alarm):
        alarm.snoozed_until = None
        if not alarm.repeat_days:
            alarm.enabled = False
            self.store.save()

import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QFileDialog, QAbstractItemView, QCheckBox,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import QTimer, Qt, QTime
from PyQt6.QtGui import QFont
from datetime import datetime

from alarm_model import Alarm, AlarmStore
from alarm_trigger import AlarmTrigger
from alert_dialog import AlertDialog


WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.store = AlarmStore()
        self.trigger = AlarmTrigger(self.store)
        self._alert_showing = False
        self._setup_ui()
        self._start_timer()
        self._refresh_table()

    def _setup_ui(self):
        self.setWindowTitle("桌面闹钟")
        self.setMinimumSize(650, 600)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 15, 20, 15)

        # --- 时间显示区 ---
        clock_group = QGroupBox("当前时间")
        clock_group.setFont(QFont("Microsoft YaHei", 10))
        clock_layout = QVBoxLayout(clock_group)

        self.date_label = QLabel()
        self.date_label.setFont(QFont("Microsoft YaHei", 14))
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clock_layout.addWidget(self.date_label)

        self.time_label = QLabel()
        self.time_label.setFont(QFont("Consolas", 36, QFont.Weight.Bold))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clock_layout.addWidget(self.time_label)

        main_layout.addWidget(clock_group)

        # --- 添加闹钟区 ---
        add_group = QGroupBox("添加闹钟")
        add_group.setFont(QFont("Microsoft YaHei", 10))
        add_layout = QGridLayout(add_group)
        add_layout.setSpacing(8)

        # 时间行
        add_layout.addWidget(QLabel("时:"), 0, 0)
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(QTime.currentTime().hour())
        self.hour_spin.setFixedWidth(60)
        add_layout.addWidget(self.hour_spin, 0, 1)

        add_layout.addWidget(QLabel("分:"), 0, 2)
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(0)
        self.minute_spin.setFixedWidth(60)
        add_layout.addWidget(self.minute_spin, 0, 3)

        add_layout.addWidget(QLabel("备注:"), 0, 4)
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("闹钟备注信息")
        add_layout.addWidget(self.note_input, 0, 5, 1, 2)

        # 铃声行
        add_layout.addWidget(QLabel("铃声:"), 1, 0)
        self.ringtone_input = QLineEdit()
        self.ringtone_input.setPlaceholderText("默认铃声")
        self.ringtone_input.setReadOnly(True)
        add_layout.addWidget(self.ringtone_input, 1, 1, 1, 5)

        ringtone_btn = QPushButton("选择")
        ringtone_btn.setFixedWidth(50)
        ringtone_btn.clicked.connect(self._select_ringtone)
        add_layout.addWidget(ringtone_btn, 1, 6)

        # 重复周期行
        add_layout.addWidget(QLabel("重复:"), 2, 0)
        repeat_layout = QHBoxLayout()
        self.repeat_checks: list[QCheckBox] = []
        for i, name in enumerate(WEEKDAY_NAMES):
            cb = QCheckBox(name)
            self.repeat_checks.append(cb)
            repeat_layout.addWidget(cb)
        add_layout.addLayout(repeat_layout, 2, 1, 1, 5)

        # 快捷选择
        quick_layout = QHBoxLayout()
        everyday_btn = QPushButton("每天")
        everyday_btn.setFixedWidth(50)
        everyday_btn.clicked.connect(lambda: self._set_repeat_all(True))
        quick_layout.addWidget(everyday_btn)
        clear_btn = QPushButton("清除")
        clear_btn.setFixedWidth(50)
        clear_btn.clicked.connect(lambda: self._set_repeat_all(False))
        quick_layout.addWidget(clear_btn)
        add_layout.addLayout(quick_layout, 2, 6)

        # 添加按钮
        add_btn = QPushButton("➕ 添加闹钟")
        add_btn.setFixedHeight(35)
        add_btn.setFont(QFont("Microsoft YaHei", 11))
        add_btn.setStyleSheet("background-color: #2ecc71; color: white; border-radius: 4px;")
        add_btn.clicked.connect(self._add_alarm)
        add_layout.addWidget(add_btn, 3, 0, 1, 7)

        main_layout.addWidget(add_group)

        # --- 闹钟列表区 ---
        list_group = QGroupBox("闹钟列表")
        list_group.setFont(QFont("Microsoft YaHei", 10))
        list_layout = QVBoxLayout(list_group)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["时间", "备注", "重复", "铃声", "状态", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        list_layout.addWidget(self.table)

        main_layout.addWidget(list_group)

    def _start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)
        self._tick()

    def _tick(self):
        now = datetime.now()
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        self.date_label.setText(f"{now.year}年{now.month:02d}月{now.day:02d}日 {weekdays[now.weekday()]}")
        self.time_label.setText(now.strftime("%H:%M:%S"))

        if not self._alert_showing:
            triggered = self.trigger.check(now)
            for alarm in triggered:
                self._show_alert(alarm)

    def _show_alert(self, alarm: Alarm):
        self._alert_showing = True
        dialog = AlertDialog(alarm, self)
        dialog.exec()
        if dialog.result_action == "snooze":
            self.trigger.snooze(alarm)
        else:
            self.trigger.dismiss(alarm)
            self._refresh_table()
        self._alert_showing = False

    def _add_alarm(self):
        repeat_days = [i for i, cb in enumerate(self.repeat_checks) if cb.isChecked()]
        alarm = Alarm(
            hour=self.hour_spin.value(),
            minute=self.minute_spin.value(),
            note=self.note_input.text().strip(),
            ringtone=self.ringtone_input.text().strip(),
            repeat_days=repeat_days,
        )
        self.store.add(alarm)
        self.note_input.clear()
        self._refresh_table()

    def _select_ringtone(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择铃声文件", "",
            "音频文件 (*.wav *.mp3 *.ogg *.flac);;所有文件 (*)"
        )
        if path:
            self.ringtone_input.setText(path)

    def _set_repeat_all(self, checked: bool):
        for cb in self.repeat_checks:
            cb.setChecked(checked)

    def _refresh_table(self):
        self.table.setRowCount(len(self.store.alarms))
        for row, alarm in enumerate(self.store.alarms):
            self.table.setItem(row, 0, QTableWidgetItem(alarm.time_str()))
            self.table.setItem(row, 1, QTableWidgetItem(alarm.note))
            self.table.setItem(row, 2, QTableWidgetItem(alarm.repeat_str()))

            ringtone_name = os.path.basename(alarm.ringtone) if alarm.ringtone else "默认"
            self.table.setItem(row, 3, QTableWidgetItem(ringtone_name))

            status_text = "已启用" if alarm.enabled else "已禁用"
            status_item = QTableWidgetItem(status_text)
            if not alarm.enabled:
                status_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 4, status_item)

            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(4)

            toggle_btn = QPushButton("禁用" if alarm.enabled else "启用")
            toggle_btn.setFixedSize(45, 26)
            toggle_btn.setStyleSheet(
                "background-color: #f39c12; color: white; border-radius: 3px; font-size: 11px;"
                if alarm.enabled else
                "background-color: #3498db; color: white; border-radius: 3px; font-size: 11px;"
            )
            alarm_id = alarm.alarm_id
            toggle_btn.clicked.connect(lambda _, aid=alarm_id: self._toggle_alarm(aid))
            btn_layout.addWidget(toggle_btn)

            del_btn = QPushButton("删除")
            del_btn.setFixedSize(45, 26)
            del_btn.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 3px; font-size: 11px;")
            del_btn.clicked.connect(lambda _, aid=alarm_id: self._delete_alarm(aid))
            btn_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 5, btn_widget)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def _toggle_alarm(self, alarm_id: str):
        self.store.toggle(alarm_id)
        self._refresh_table()

    def _delete_alarm(self, alarm_id: str):
        self.store.remove(alarm_id)
        self._refresh_table()

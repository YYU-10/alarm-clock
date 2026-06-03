import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from alarm_model import Alarm


class AlertDialog(QDialog):
    def __init__(self, alarm: Alarm, parent=None):
        super().__init__(parent)
        self.alarm = alarm
        self.result_action = "dismiss"
        self._player = None
        self._audio_output = None
        self._setup_ui()
        self._play_sound()

    def _setup_ui(self):
        self.setWindowTitle("闹钟提醒")
        self.setFixedSize(380, 220)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 25, 30, 25)

        time_label = QLabel(f"⏰ {self.alarm.time_str()}")
        time_label.setFont(QFont("Microsoft YaHei", 28, QFont.Weight.Bold))
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(time_label)

        if self.alarm.note:
            note_label = QLabel(self.alarm.note)
            note_label.setFont(QFont("Microsoft YaHei", 14))
            note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            note_label.setWordWrap(True)
            layout.addWidget(note_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        snooze_btn = QPushButton("延后5分钟")
        snooze_btn.setFixedHeight(38)
        snooze_btn.setFont(QFont("Microsoft YaHei", 11))
        snooze_btn.clicked.connect(self._on_snooze)
        btn_layout.addWidget(snooze_btn)

        dismiss_btn = QPushButton("关闭闹钟")
        dismiss_btn.setFixedHeight(38)
        dismiss_btn.setFont(QFont("Microsoft YaHei", 11))
        dismiss_btn.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 4px;")
        dismiss_btn.clicked.connect(self._on_dismiss)
        btn_layout.addWidget(dismiss_btn)

        layout.addLayout(btn_layout)

    def _play_sound(self):
        ringtone_path = self.alarm.ringtone
        if not ringtone_path or not os.path.exists(ringtone_path):
            default_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "ringtones", "default.wav"
            )
            if os.path.exists(default_path):
                ringtone_path = default_path
            else:
                return

        from PyQt6.QtCore import QUrl
        self._audio_output = QAudioOutput()
        self._audio_output.setVolume(0.8)
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)
        self._player.setSource(QUrl.fromLocalFile(ringtone_path))
        self._player.setLoops(QMediaPlayer.Loops.Infinite)
        self._player.play()

    def _stop_sound(self):
        if self._player:
            self._player.stop()
            self._player = None
        if self._audio_output:
            self._audio_output = None

    def _on_snooze(self):
        self.result_action = "snooze"
        self._stop_sound()
        self.accept()

    def _on_dismiss(self):
        self.result_action = "dismiss"
        self._stop_sound()
        self.accept()

    def closeEvent(self, event):
        self._stop_sound()
        self.result_action = "dismiss"
        super().closeEvent(event)

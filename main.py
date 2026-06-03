import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from ui_main import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 创建默认铃声目录
    ringtone_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ringtones")
    os.makedirs(ringtone_dir, exist_ok=True)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

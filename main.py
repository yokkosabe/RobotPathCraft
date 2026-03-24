"""Entry point for RobotPathCraft desktop application."""

import sys
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox

from gui.main_window import MainWindow


def main() -> int:
    """Start Qt application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Критическая ошибка", f"{exc}\n\n{traceback.format_exc()}")
        raise
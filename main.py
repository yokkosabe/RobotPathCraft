"""Точка входа в десктопное приложение RobotPathCraft."""

import sys
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox

from gui.main_window import MainWindow


def main() -> int:
    """Запуск Qt-приложения."""
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
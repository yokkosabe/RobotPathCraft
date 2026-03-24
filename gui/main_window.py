"""Главное окно приложения RobotPathCraft."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from algorithms.astar import astar_search
from algorithms.rrt import rrt_search
from algorithms.smoother import shortcut_smooth
from analysis.recommender import build_recommendation, path_length
from gui.canvas_widget import CanvasWidget
from gui.control_panel import ControlPanel
from map_loader import MapData
from map_loader.csv_loader import load_csv_map
from map_loader.image_loader import load_image_map
from map_loader.json_loader import load_json_map


class PlannerWorker(QObject):
    """Фоновый обработчик для расчёта пути."""

    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, grid: np.ndarray, params: dict) -> None:
        super().__init__()
        self.grid = grid
        self.params = params

    def run(self) -> None:
        try:
            self.progress.emit(15)
            algo = self.params["algorithm"]
            start = self.params["start"]
            goal = self.params["goal"]
            step = self.params["step"]
            goal_tol = self.params["goal_tol"]
            path = None
            edges = []

            if algo == "A*":
                path = astar_search(self.grid, start, goal, goal_radius=goal_tol, step=max(1, int(step)))
                self.progress.emit(75)
            else:
                path, edges = rrt_search(
                    self.grid,
                    start,
                    goal,
                    step_size=float(step),
                    goal_radius=float(goal_tol),
                    max_iter=5000,
                )
                self.progress.emit(75)

            if path is None:
                self.failed.emit("Путь не найден. Проверьте карту, старт/цель и параметры.")
                return

            if self.params["smoothing"]:
                path = shortcut_smooth(self.grid, path)

            self.progress.emit(100)
            self.finished.emit({"path": path, "rrt_edges": edges})
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    """Основное окно с элементами управления и визуализацией."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RobotPathCraft")
        self.resize(1300, 800)

        self.map_data: MapData | None = None
        self.current_path: list[tuple[float, float]] = []
        self.current_edges: list = []
        self.selecting_start = True

        self.worker_thread: QThread | None = None
        self.worker: PlannerWorker | None = None

        self._build_ui()
        self._create_menu()
        self._apply_styles()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        self.panel = ControlPanel()
        self.canvas = CanvasWidget()

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(10)
        self.stats_label = QLabel("Длина пути: - | Время: -")
        self.stats_label.setObjectName("statsLabel")
        self.recommendations = QPlainTextEdit()
        self.recommendations.setObjectName("recommendationsPanel")
        self.recommendations.setReadOnly(True)
        self.recommendations.setPlaceholderText("После расчёта здесь появятся рекомендации.")

        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(12, 10, 12, 10)
        stats_layout.addWidget(self.stats_label)

        right_layout.addWidget(self.canvas, stretch=5)
        right_layout.addWidget(self.progress)
        right_layout.addWidget(stats_frame)
        right_layout.addWidget(self.recommendations, stretch=2)

        splitter = QSplitter()
        splitter.setObjectName("mainSplitter")
        splitter.addWidget(self.panel)
        splitter.addWidget(right)
        splitter.setSizes([320, 980])
        layout.addWidget(splitter)

        self.panel.load_map_btn.clicked.connect(self.load_map)
        self.panel.calculate_btn.clicked.connect(self.calculate_path)
        self.panel.reset_btn.clicked.connect(self.reset)
        self.panel.save_image_btn.clicked.connect(self.save_image)
        self.canvas.point_clicked.connect(self.on_map_clicked)

    def _create_menu(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("Файл")
        view_menu = menu.addMenu("Вид")
        help_menu = menu.addMenu("Помощь")

        load_action = file_menu.addAction("Загрузить карту")
        load_action.triggered.connect(self.load_map)

        save_session_action = file_menu.addAction("Сохранить сеанс")
        save_session_action.triggered.connect(self.save_session)

        load_session_action = file_menu.addAction("Загрузить сеанс")
        load_session_action.triggered.connect(self.load_session)

        save_img_action = file_menu.addAction("Сохранить изображение")
        save_img_action.triggered.connect(self.save_image)

        zoom_in = view_menu.addAction("Увеличить")
        zoom_out = view_menu.addAction("Уменьшить")
        zoom_reset = view_menu.addAction("Сбросить масштаб")
        zoom_in.triggered.connect(lambda: self._zoom(0.8))
        zoom_out.triggered.connect(lambda: self._zoom(1.25))
        zoom_reset.triggered.connect(self._zoom_reset)

        about_action = help_menu.addAction("О программе")
        about_action.triggered.connect(
            lambda: QMessageBox.information(
                self,
                "RobotPathCraft",
                "RobotPathCraft\nПроектирование траекторий для мехатронных систем.",
            )
        )

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #edf1f7;
            }
            QMenuBar, QMenu {
                background: #ffffff;
                color: #1f2a37;
            }
            QMenuBar::item:selected, QMenu::item:selected {
                background: #e9efff;
            }
            QGroupBox {
                background: #ffffff;
                border: 1px solid #d7dfeb;
                border-radius: 10px;
                margin-top: 12px;
                padding: 10px;
                font-weight: 600;
                color: #1f2a37;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
            }
            QPushButton {
                border-radius: 9px;
                border: 1px solid #c6d0e0;
                background: #ffffff;
                color: #1f2a37;
                padding: 6px 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #f3f6fb;
            }
            QPushButton#primaryButton {
                background: #1f6feb;
                color: #ffffff;
                border: 1px solid #1757b8;
            }
            QPushButton#primaryButton:hover {
                background: #2a7df7;
            }
            QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit {
                background: #ffffff;
                border: 1px solid #cfd8e6;
                border-radius: 7px;
                padding: 4px 6px;
                color: #1f2a37;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {
                border: 1px solid #5b8def;
            }
            QProgressBar {
                border: 1px solid #ced7e6;
                border-radius: 5px;
                background: #f2f5fb;
            }
            QProgressBar::chunk {
                border-radius: 5px;
                background: #2f81f7;
            }
            QFrame#statsFrame {
                background: #ffffff;
                border: 1px solid #d7dfeb;
                border-radius: 9px;
            }
            QLabel#statsLabel {
                color: #243247;
                font-size: 13px;
                font-weight: 600;
            }
            QPlainTextEdit#recommendationsPanel {
                background: #fcfdff;
                border: 1px solid #d7dfeb;
                border-radius: 10px;
                font-family: "Consolas", "Segoe UI";
                font-size: 12px;
            }
            """
        )

    def _zoom(self, factor: float) -> None:
        x0, x1 = self.canvas.ax.get_xlim()
        y0, y1 = self.canvas.ax.get_ylim()
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hx = (x1 - x0) * factor / 2
        hy = (y1 - y0) * factor / 2
        self.canvas.ax.set_xlim(cx - hx, cx + hx)
        self.canvas.ax.set_ylim(cy - hy, cy + hy)
        self.canvas.canvas.draw_idle()

    def _zoom_reset(self) -> None:
        if not self.map_data:
            return
        h, w = self.map_data.grid.shape
        self.canvas.ax.set_xlim(0, w)
        self.canvas.ax.set_ylim(h, 0)
        self.canvas.canvas.draw_idle()

    def _ensure_map(self) -> bool:
        if self.map_data is None:
            QMessageBox.warning(self, "Нет карты", "Сначала загрузите карту рабочего пространства.")
            return False
        return True

    def _is_valid_point(self, x: int, y: int) -> bool:
        if not self.map_data:
            return False
        h, w = self.map_data.grid.shape
        return 0 <= x < w and 0 <= y < h

    def _validate_inputs(self) -> bool:
        if not self._ensure_map():
            return False

        sx, sy = self.panel.start_x.value(), self.panel.start_y.value()
        gx, gy = self.panel.goal_x.value(), self.panel.goal_y.value()

        ok = True
        for spin in (self.panel.start_x, self.panel.start_y, self.panel.goal_x, self.panel.goal_y):
            spin.setStyleSheet("")

        if not self._is_valid_point(sx, sy):
            self.panel.start_x.setStyleSheet("background-color: #ffd6d6;")
            self.panel.start_y.setStyleSheet("background-color: #ffd6d6;")
            ok = False
        if not self._is_valid_point(gx, gy):
            self.panel.goal_x.setStyleSheet("background-color: #ffd6d6;")
            self.panel.goal_y.setStyleSheet("background-color: #ffd6d6;")
            ok = False

        if not ok:
            QMessageBox.warning(self, "Некорректные координаты", "Старт или цель вне границ карты.")
            return False

        if self.map_data.grid[sy, sx] == 1 or self.map_data.grid[gy, gx] == 1:
            QMessageBox.warning(self, "Препятствие", "Старт или цель находятся внутри препятствия.")
            return False

        if self.panel.speed.value() <= 0:
            self.panel.speed.setStyleSheet("background-color: #ffd6d6;")
            QMessageBox.warning(self, "Некорректная скорость", "Скорость должна быть положительной.")
            return False
        self.panel.speed.setStyleSheet("")
        return True

    def load_map(self) -> None:
        try:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Открыть карту",
                "",
                "Map files (*.png *.jpg *.jpeg *.json *.csv)",
            )
            if not path:
                return

            ext = Path(path).suffix.lower()
            if ext in {".png", ".jpg", ".jpeg"}:
                threshold, ok = self._ask_threshold()
                if not ok:
                    return
                self.map_data = load_image_map(path, threshold)
            elif ext == ".json":
                self.map_data = load_json_map(path)
            elif ext == ".csv":
                self.map_data = load_csv_map(path)
            else:
                raise ValueError("Неподдерживаемый формат карты.")

            self.current_path = []
            self.current_edges = []
            self.recommendations.clear()
            self.progress.setValue(0)

            h, w = self.map_data.grid.shape
            self.panel.start_x.setRange(0, w - 1)
            self.panel.goal_x.setRange(0, w - 1)
            self.panel.start_y.setRange(0, h - 1)
            self.panel.goal_y.setRange(0, h - 1)

            if self.map_data.start:
                self.panel.start_x.setValue(self.map_data.start[0])
                self.panel.start_y.setValue(self.map_data.start[1])
            else:
                self.panel.start_x.setValue(0)
                self.panel.start_y.setValue(0)

            if self.map_data.goal:
                self.panel.goal_x.setValue(self.map_data.goal[0])
                self.panel.goal_y.setValue(self.map_data.goal[1])
            else:
                self.panel.goal_x.setValue(max(0, w - 1))
                self.panel.goal_y.setValue(max(0, h - 1))

            self._redraw()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка загрузки", f"Не удалось загрузить карту:\n{exc}")

    def _ask_threshold(self) -> tuple[int, bool]:
        from PyQt6.QtWidgets import QInputDialog

        val, ok = QInputDialog.getInt(
            self,
            "Порог бинаризации",
            "Тёмные пиксели считаются препятствиями. Введите порог (0..255):",
            127,
            0,
            255,
            1,
        )
        return val, ok

    def on_map_clicked(self, x: int, y: int) -> None:
        if not self._ensure_map() or not self._is_valid_point(x, y):
            return
        if self.selecting_start:
            self.panel.start_x.setValue(x)
            self.panel.start_y.setValue(y)
        else:
            self.panel.goal_x.setValue(x)
            self.panel.goal_y.setValue(y)
        self.selecting_start = not self.selecting_start
        self._redraw()

    def calculate_path(self) -> None:
        try:
            if not self._validate_inputs():
                return

            params = {
                "start": (self.panel.start_x.value(), self.panel.start_y.value()),
                "goal": (self.panel.goal_x.value(), self.panel.goal_y.value()),
                "algorithm": self.panel.algorithm.currentText(),
                "speed": self.panel.speed.value(),
                "turn_radius": self.panel.turn_radius.value(),
                "step": self.panel.step.value(),
                "goal_tol": self.panel.goal_tol.value(),
                "smoothing": self.panel.smoothing.isChecked(),
            }

            self.panel.calculate_btn.setEnabled(False)
            self.progress.setValue(0)

            self.worker_thread = QThread(self)
            self.worker = PlannerWorker(self.map_data.grid, params)
            self.worker.moveToThread(self.worker_thread)
            self.worker_thread.started.connect(self.worker.run)
            self.worker.progress.connect(self.progress.setValue)
            self.worker.finished.connect(lambda res: self._on_calc_success(res, params))
            self.worker.failed.connect(self._on_calc_error)
            self.worker.finished.connect(self._cleanup_worker)
            self.worker.failed.connect(self._cleanup_worker)
            self.worker_thread.start()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))

    def _cleanup_worker(self) -> None:
        self.panel.calculate_btn.setEnabled(True)
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait(1000)
        self.worker_thread = None
        self.worker = None

    def _on_calc_success(self, result: dict, params: dict) -> None:
        self.current_path = result["path"]
        self.current_edges = result["rrt_edges"]
        self._redraw()
        length = path_length(self.current_path)
        t = length / params["speed"] if params["speed"] > 0 else float("inf")
        self.stats_label.setText(f"Длина пути: {length:.2f} ед. | Время: {t:.2f} с")
        self.recommendations.setPlainText(
            build_recommendation(
                self.map_data.grid,
                self.current_path,
                params["speed"],
                params["turn_radius"],
            )
        )

    def _on_calc_error(self, msg: str) -> None:
        self.progress.setValue(0)
        QMessageBox.warning(self, "Расчёт не выполнен", msg)

    def _redraw(self) -> None:
        if not self.map_data:
            return
        start = (self.panel.start_x.value(), self.panel.start_y.value())
        goal = (self.panel.goal_x.value(), self.panel.goal_y.value())
        self.canvas.draw_scene(
            self.map_data.grid,
            start=start,
            goal=goal,
            path=self.current_path,
            rrt_edges=self.current_edges,
            show_rrt_tree=self.panel.algorithm.currentText() == "RRT",
        )

    def reset(self) -> None:
        self.current_path = []
        self.current_edges = []
        self.stats_label.setText("Длина пути: - | Время: -")
        self.recommendations.clear()
        self.progress.setValue(0)
        self._redraw()

    def save_image(self) -> None:
        if not self._ensure_map():
            return
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить изображение", "", "PNG Image (*.png)")
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        try:
            self.canvas.figure.savefig(path, dpi=150)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка сохранения", str(exc))

    def save_session(self) -> None:
        if not self._ensure_map():
            return
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить сеанс", "", "JSON (*.json)")
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            data = {
                "grid": self.map_data.grid.tolist(),
                "start": [self.panel.start_x.value(), self.panel.start_y.value()],
                "goal": [self.panel.goal_x.value(), self.panel.goal_y.value()],
                "algorithm": self.panel.algorithm.currentText(),
                "speed": self.panel.speed.value(),
                "turn_radius": self.panel.turn_radius.value(),
                "step": self.panel.step.value(),
                "goal_tol": self.panel.goal_tol.value(),
                "smoothing": self.panel.smoothing.isChecked(),
            }
            Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка сохранения", str(exc))

    def load_session(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Загрузить сеанс", "", "JSON (*.json)")
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            grid = np.array(data["grid"], dtype=np.uint8)
            self.map_data = MapData(grid=grid)

            h, w = grid.shape
            self.panel.start_x.setRange(0, w - 1)
            self.panel.goal_x.setRange(0, w - 1)
            self.panel.start_y.setRange(0, h - 1)
            self.panel.goal_y.setRange(0, h - 1)

            self.panel.start_x.setValue(int(data["start"][0]))
            self.panel.start_y.setValue(int(data["start"][1]))
            self.panel.goal_x.setValue(int(data["goal"][0]))
            self.panel.goal_y.setValue(int(data["goal"][1]))

            idx = self.panel.algorithm.findText(data.get("algorithm", "A*"))
            self.panel.algorithm.setCurrentIndex(max(0, idx))
            self.panel.speed.setValue(float(data.get("speed", 20.0)))
            self.panel.turn_radius.setValue(float(data.get("turn_radius", 2.0)))
            self.panel.step.setValue(float(data.get("step", 3.0)))
            self.panel.goal_tol.setValue(float(data.get("goal_tol", 3.0)))
            self.panel.smoothing.setChecked(bool(data.get("smoothing", True)))

            self.current_path = []
            self.current_edges = []
            self.stats_label.setText("Длина пути: - | Время: -")
            self.recommendations.clear()
            self.progress.setValue(0)
            self._redraw()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка загрузки", str(exc))

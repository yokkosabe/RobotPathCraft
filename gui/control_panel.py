"""Панель управления со всеми параметрами траектории."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class ControlPanel(QWidget):
    """Левая панель с загрузкой карты и параметрами алгоритма."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        self.load_map_btn = QPushButton("Загрузить карту")
        self.calculate_btn = QPushButton("Рассчитать")
        self.reset_btn = QPushButton("Сброс")
        self.save_image_btn = QPushButton("Сохранить изображение")
        self.load_map_btn.setObjectName("secondaryButton")
        self.calculate_btn.setObjectName("primaryButton")
        self.reset_btn.setObjectName("secondaryButton")
        self.save_image_btn.setObjectName("secondaryButton")
        for btn in (self.load_map_btn, self.calculate_btn, self.reset_btn, self.save_image_btn):
            btn.setMinimumHeight(38)

        group = QGroupBox("Параметры движения")
        form = QFormLayout(group)
        form.setLabelAlignment(form.labelAlignment())
        form.setVerticalSpacing(9)
        form.setHorizontalSpacing(10)

        self.start_x = QSpinBox()
        self.start_y = QSpinBox()
        self.goal_x = QSpinBox()
        self.goal_y = QSpinBox()
        for spin in (self.start_x, self.start_y, self.goal_x, self.goal_y):
            spin.setRange(0, 5000)

        self.algorithm = QComboBox()
        self.algorithm.addItems(["A*", "RRT"])

        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.01, 10000.0)
        self.speed.setValue(20.0)
        self.speed.setSingleStep(0.5)

        self.turn_radius = QDoubleSpinBox()
        self.turn_radius.setRange(0.0, 1000.0)
        self.turn_radius.setValue(2.0)
        self.turn_radius.setSingleStep(0.5)

        self.step = QDoubleSpinBox()
        self.step.setRange(1.0, 100.0)
        self.step.setValue(3.0)
        self.step.setSingleStep(1.0)

        self.goal_tol = QDoubleSpinBox()
        self.goal_tol.setRange(0.0, 200.0)
        self.goal_tol.setValue(3.0)
        self.goal_tol.setSingleStep(0.5)

        self.smoothing = QCheckBox("Включить сглаживание")
        self.smoothing.setChecked(True)

        form.addRow("Старт X:", self.start_x)
        form.addRow("Старт Y:", self.start_y)
        form.addRow("Цель X:", self.goal_x)
        form.addRow("Цель Y:", self.goal_y)
        form.addRow("Алгоритм:", self.algorithm)
        form.addRow("Макс. скорость:", self.speed)
        form.addRow("Радиус поворота:", self.turn_radius)
        form.addRow("Шаг сетки/расширения:", self.step)
        form.addRow("Допустимое отклонение:", self.goal_tol)
        form.addRow(self.smoothing)

        root.addWidget(self.load_map_btn)
        root.addWidget(group)
        root.addWidget(self.calculate_btn)
        root.addWidget(self.reset_btn)
        root.addWidget(self.save_image_btn)
        root.addStretch(1)

        self._setup_tooltips()

    def _setup_tooltips(self) -> None:
        self.load_map_btn.setToolTip("Загрузить карту PNG/JPG/JSON/CSV.")
        self.calculate_btn.setToolTip("Запустить расчёт траектории.")
        self.reset_btn.setToolTip("Сбросить путь и рекомендации.")
        self.save_image_btn.setToolTip("Сохранить визуализацию в изображение.")
        self.algorithm.setToolTip("Выбор алгоритма поиска пути: A* или RRT.")
        self.speed.setToolTip("Максимальная скорость для оценки времени движения.")
        self.turn_radius.setToolTip("Минимальный радиус поворота для рекомендаций.")
        self.step.setToolTip("Шаг A* по сетке / шаг расширения для RRT.")
        self.goal_tol.setToolTip("Радиус достижения цели.")
        self.smoothing.setToolTip("Постобработка маршрута методом shortcutting.")

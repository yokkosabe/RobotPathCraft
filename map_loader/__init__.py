"""Утилиты загрузки карт для RobotPathCraft."""

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class MapData:
    """Контейнер для сетки занятости и необязательных точек старта/цели."""

    grid: np.ndarray  # Двумерная матрица: 0 — свободно, 1 — препятствие
    start: Optional[tuple[int, int]] = None
    goal: Optional[tuple[int, int]] = None

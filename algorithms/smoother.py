"""Сглаживание пути и простые геометрические утилиты."""

from __future__ import annotations

import math

import numpy as np


def line_of_sight(grid: np.ndarray, a: tuple[float, float], b: tuple[float, float]) -> bool:
    """Проверить, что отрезок не пересекает препятствия."""
    steps = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) * 2))
    h, w = grid.shape
    for i in range(steps + 1):
        t = i / steps
        x = int(round(a[0] + (b[0] - a[0]) * t))
        y = int(round(a[1] + (b[1] - a[1]) * t))
        if not (0 <= x < w and 0 <= y < h):
            return False
        if grid[y, x] == 1:
            return False
    return True


def shortcut_smooth(grid: np.ndarray, path: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Удалить промежуточные точки при наличии прямой видимости."""
    if len(path) <= 2:
        return path
    smoothed = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1:
            if line_of_sight(grid, path[i], path[j]):
                break
            j -= 1
        smoothed.append(path[j])
        i = j
    return smoothed

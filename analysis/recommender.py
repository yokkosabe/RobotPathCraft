"""Метрики и текстовые рекомендации для найденных траекторий."""

from __future__ import annotations

import math

import numpy as np


def path_length(path: list[tuple[float, float]]) -> float:
    """Вычислить длину ломаной траектории."""
    if len(path) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(path)):
        total += math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])
    return total


def turn_count(path: list[tuple[float, float]], angle_threshold_deg: float = 20.0) -> int:
    """Посчитать повороты по порогу изменения направления."""
    if len(path) < 3:
        return 0
    turns = 0
    thr = math.radians(angle_threshold_deg)
    for i in range(1, len(path) - 1):
        v1 = (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])
        v2 = (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
        n1 = math.hypot(v1[0], v1[1])
        n2 = math.hypot(v2[0], v2[1])
        if n1 == 0 or n2 == 0:
            continue
        dot = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
        if math.acos(dot) >= thr:
            turns += 1
    return turns


def min_clearance(grid: np.ndarray, path: list[tuple[float, float]]) -> float:
    """Оценить минимальное расстояние от пути до препятствий."""
    obs = np.argwhere(grid == 1)
    if len(obs) == 0 or len(path) == 0:
        return float("inf")
    best = float("inf")
    for x, y in path:
        d = np.sqrt((obs[:, 1] - x) ** 2 + (obs[:, 0] - y) ** 2).min()
        best = min(best, float(d))
    return best


def build_recommendation(
    grid: np.ndarray,
    path: list[tuple[float, float]],
    speed: float,
    min_turn_radius: float,
) -> str:
    """Сформировать отчёт по траектории для пользователя."""
    length = path_length(path)
    turns = turn_count(path)
    clearance = min_clearance(grid, path)
    travel_time = length / speed if speed > 0 else float("inf")

    lines = [
        "✅ Траектория найдена",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📏 Длина пути:         {length:.2f} ед.",
        f"⏱  Расчётное время:   {travel_time:.2f} с (при v_max = {speed:.2f} ед/с)",
        f"↩  Количество поворотов: {turns}",
        f"📐 Мин. зазор до препятствий: {clearance:.2f} ед.",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "Рекомендации:",
    ]

    if turns > 12:
        lines.append("• Маршрут содержит много поворотов: рассмотрите увеличение шага/сглаживание.")
    elif turns > 6:
        lines.append("• Число поворотов умеренное: проверьте комфортный профиль скорости.")
    else:
        lines.append("• Траектория достаточно плавная.")

    if clearance < 2.0:
        lines.append("• Критически малый зазор: снизьте скорость и увеличьте запас безопасности.")
    elif clearance < max(2.0, min_turn_radius):
        lines.append("• Есть узкие участки: рекомендуется осторожный проход на сниженной скорости.")
    else:
        lines.append("• Запас по расстоянию до препятствий приемлем.")

    if speed > 0 and travel_time > 20:
        lines.append("• Расчётное время движения высокое: попробуйте альтернативный маршрут.")

    return "\n".join(lines)

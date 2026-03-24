"""A* pathfinding on occupancy grid."""

from __future__ import annotations

import heapq
import math
from typing import Optional

import numpy as np


def _heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _neighbors(node: tuple[int, int], h: int, w: int) -> list[tuple[int, int]]:
    x, y = node
    result = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                result.append((nx, ny))
    return result


def astar_search(
    grid: np.ndarray,
    start: tuple[int, int],
    goal: tuple[int, int],
    goal_radius: float = 0.0,
    step: int = 1,
) -> Optional[list[tuple[int, int]]]:
    """Find path from start to goal over occupancy grid."""
    h, w = grid.shape
    if step < 1:
        step = 1
    if grid[start[1], start[0]] == 1 or grid[goal[1], goal[0]] == 1:
        return None

    open_heap: list[tuple[float, tuple[int, int]]] = []
    heapq.heappush(open_heap, (0.0, start))
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    g_score: dict[tuple[int, int], float] = {start: 0.0}
    visited = set()

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current in visited:
            continue
        visited.add(current)

        if _heuristic(current, goal) <= goal_radius:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        cx, cy = current
        for nx, ny in _neighbors((cx, cy), h, w):
            if abs(nx - cx) > step or abs(ny - cy) > step:
                continue
            if grid[ny, nx] == 1:
                continue

            tentative = g_score[current] + math.hypot(nx - cx, ny - cy)
            if tentative < g_score.get((nx, ny), float("inf")):
                came_from[(nx, ny)] = current
                g_score[(nx, ny)] = tentative
                f_score = tentative + _heuristic((nx, ny), goal)
                heapq.heappush(open_heap, (f_score, (nx, ny)))
    return None

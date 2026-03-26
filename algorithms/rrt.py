from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class Node:
    x: float
    y: float
    parent: int


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _is_free(grid: np.ndarray, x: float, y: float) -> bool:
    h, w = grid.shape
    xi, yi = int(round(x)), int(round(y))
    return 0 <= xi < w and 0 <= yi < h and grid[yi, xi] == 0


def _line_collision_free(grid: np.ndarray, a: tuple[float, float], b: tuple[float, float]) -> bool:
    dist = max(2, int(_distance(a, b) * 2))
    for i in range(dist + 1):
        t = i / dist
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + (b[1] - a[1]) * t
        if not _is_free(grid, x, y):
            return False
    return True


def rrt_search(
    grid: np.ndarray,
    start: tuple[int, int],
    goal: tuple[int, int],
    step_size: float = 5.0,
    goal_radius: float = 5.0,
    max_iter: int = 5000,
) -> tuple[Optional[list[tuple[float, float]]], list[tuple[tuple[float, float], tuple[float, float]]]]:
    """Запустить RRT и вернуть путь и рёбра дерева."""
    if not _is_free(grid, start[0], start[1]) or not _is_free(grid, goal[0], goal[1]):
        return None, []

    h, w = grid.shape
    nodes: list[Node] = [Node(float(start[0]), float(start[1]), -1)]
    edges: list[tuple[tuple[float, float], tuple[float, float]]] = []

    for _ in range(max_iter):
        if random.random() < 0.15:
            sample = (float(goal[0]), float(goal[1]))
        else:
            sample = (random.uniform(0, w - 1), random.uniform(0, h - 1))

        nearest_idx = min(
            range(len(nodes)),
            key=lambda i: _distance((nodes[i].x, nodes[i].y), sample),
        )
        nearest = nodes[nearest_idx]
        angle = math.atan2(sample[1] - nearest.y, sample[0] - nearest.x)
        new_x = nearest.x + step_size * math.cos(angle)
        new_y = nearest.y + step_size * math.sin(angle)

        if not _is_free(grid, new_x, new_y):
            continue
        if not _line_collision_free(grid, (nearest.x, nearest.y), (new_x, new_y)):
            continue

        nodes.append(Node(new_x, new_y, nearest_idx))
        edges.append(((nearest.x, nearest.y), (new_x, new_y)))
        new_idx = len(nodes) - 1

        if _distance((new_x, new_y), (goal[0], goal[1])) <= goal_radius:
            if _line_collision_free(grid, (new_x, new_y), (goal[0], goal[1])):
                nodes.append(Node(float(goal[0]), float(goal[1]), new_idx))
                edges.append(((new_x, new_y), (float(goal[0]), float(goal[1]))))
                path = []
                idx = len(nodes) - 1
                while idx != -1:
                    n = nodes[idx]
                    path.append((n.x, n.y))
                    idx = n.parent
                path.reverse()
                return path, edges
    return None, edges

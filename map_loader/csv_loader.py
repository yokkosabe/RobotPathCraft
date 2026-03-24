"""Загрузка карты занятости из CSV-матрицы."""

from pathlib import Path

import numpy as np

from map_loader import MapData


def load_csv_map(path: str) -> MapData:
    """Загрузить карту из CSV, где 0 — свободно, 1 — препятствие."""
    arr = np.loadtxt(Path(path), delimiter=",", dtype=np.int32)
    if arr.ndim != 2:
        raise ValueError("CSV-карта должна быть двумерной матрицей.")
    grid = (arr > 0).astype(np.uint8)
    return MapData(grid=grid)

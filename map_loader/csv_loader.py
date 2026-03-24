"""Load occupancy map from CSV matrix."""

from pathlib import Path

import numpy as np

from map_loader import MapData


def load_csv_map(path: str) -> MapData:
    """Load map from CSV where 0=free and 1=obstacle."""
    arr = np.loadtxt(Path(path), delimiter=",", dtype=np.int32)
    if arr.ndim != 2:
        raise ValueError("CSV map must be a 2D matrix.")
    grid = (arr > 0).astype(np.uint8)
    return MapData(grid=grid)

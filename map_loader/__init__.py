"""Map loading utilities for RobotPathCraft."""

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class MapData:
    """Container for occupancy map and optional start/goal points."""

    grid: np.ndarray  # 2D array: 0 free, 1 obstacle
    start: Optional[tuple[int, int]] = None
    goal: Optional[tuple[int, int]] = None

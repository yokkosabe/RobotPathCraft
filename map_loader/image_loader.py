"""Load occupancy map from image files."""

from pathlib import Path

import numpy as np
from PIL import Image

from map_loader import MapData


def load_image_map(path: str, threshold: int = 127) -> MapData:
    """Load image and convert to binary occupancy map."""
    img = Image.open(Path(path)).convert("L")
    arr = np.asarray(img, dtype=np.uint8)
    # Dark pixels are obstacles, bright pixels are free space.
    grid = (arr < threshold).astype(np.uint8)
    return MapData(grid=grid)

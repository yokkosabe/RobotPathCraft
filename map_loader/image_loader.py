"""Загрузка карты занятости из файлов изображений."""

from pathlib import Path

import numpy as np
from PIL import Image

from map_loader import MapData


def load_image_map(path: str, threshold: int = 127) -> MapData:
    """Загрузить изображение и преобразовать в бинарную карту занятости."""
    img = Image.open(Path(path)).convert("L")
    arr = np.asarray(img, dtype=np.uint8)
    # Тёмные пиксели считаются препятствиями, светлые — свободным пространством.
    grid = (arr < threshold).astype(np.uint8)
    return MapData(grid=grid)

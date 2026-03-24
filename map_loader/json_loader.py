"""Load occupancy map from JSON files."""

import json
from pathlib import Path

import numpy as np

from map_loader import MapData


def load_json_map(path: str) -> MapData:
    """Load map from JSON with width/height/obstacles/start/goal."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    width = int(data["width"])
    height = int(data["height"])
    grid = np.zeros((height, width), dtype=np.uint8)
    for item in data.get("obstacles", []):
        x, y = int(item[0]), int(item[1])
        if 0 <= x < width and 0 <= y < height:
            grid[y, x] = 1
    start = tuple(data["start"]) if "start" in data and data["start"] else None
    goal = tuple(data["goal"]) if "goal" in data and data["goal"] else None
    if start:
        start = (int(start[0]), int(start[1]))
    if goal:
        goal = (int(goal[0]), int(goal[1]))
    return MapData(grid=grid, start=start, goal=goal)

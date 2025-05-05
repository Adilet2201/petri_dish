# bacteria_simulation/simulation/spatial_grid.py
from collections import defaultdict
import math

class SpatialHash:
    def __init__(self, cell_size: int):
        self.cell = cell_size
        self.buckets = defaultdict(list)

    def _key(self, x, y):
        return (int(x // self.cell), int(y // self.cell))

    def clear(self):
        self.buckets.clear()

    def add(self, obj):
        self.buckets[self._key(obj.x, obj.y)].append(obj)

    def query_radius(self, x, y, radius):
        r_cells = int(math.ceil(radius / self.cell))
        cx, cy = self._key(x, y)
        for dy in range(-r_cells, r_cells + 1):
            for dx in range(-r_cells, r_cells + 1):
                for o in self.buckets.get((cx + dx, cy + dy), ()):
                    if (o.x - x) ** 2 + (o.y - y) ** 2 <= radius ** 2:
                        yield o

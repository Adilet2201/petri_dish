import numpy as np
from .spatial_grid import SpatialHash
from .organisms    import Bacterium, Fungus


class Environment:
    """Мир размером 500×500, совпадающий с канвой Pixi."""

    def __init__(self, width: int = 500, height: int = 500, grid_size: int = 60):
        self.width, self.height = width, height
        self.grid_size          = grid_size

        # физ-хим параметры
        self.temperature      = 25.0
        self.ph               = 7.0
        self.speed_multiplier = 1.0

        # карта питательных веществ
        self.nutrient_map = np.full((grid_size, grid_size), 6.0, dtype=np.float32)

        # сущности
        self.organisms = []     # живые + трупы
        self.newborn   = []     # пополняется за шаг
        self.grid      = SpatialHash(cell_size=20)

        self.antibiotic_clouds = []   # (x, y, r, level, ttl)
        self.ticks = 0               # счётчик сим-минут

    # ───────── helpers ─────────
    def cell_index(self, x: float, y: float) -> tuple[int, int]:
        col = min(int(x / self.width  * self.grid_size), self.grid_size - 1)
        row = min(int(y / self.height * self.grid_size), self.grid_size - 1)
        return row, col

    # ───────── основной цикл ─────────
    def update(self, steps: int = 1):
        for _ in range(steps):
            self._step()

    def _step(self):
        self.ticks += 1

        # (1) spatial-hash
        self.grid.clear()
        for o in self.organisms:
            self.grid.add(o)

        # (2) обновление организмов
        for o in self.organisms:
            o.update(self)

        # (3) антибиотик
        self._antibiotic_phase()

        # (4) новорождённые
        self.organisms.extend(self.newborn)
        self.newborn.clear()

        # (5) трупы остаются, но не движутся
        for o in self.organisms:
            if not o.is_alive:
                o.vx = o.vy = 0
                o.dead_body = True

        # (6) диффузия / распад
        if np.random.randint(5) == 0:
            if self.ticks <= 60 * 30:         # первые 30 сим-минут
                self._diffuse(replenish=True)
            else:
                self._diffuse()

    # ──────────────────────────
    # АНТИБИОТИК
    # ──────────────────────────
    def _antibiotic_phase(self):
        next_clouds = []
        for x, y, r, level, ttl in self.antibiotic_clouds:
            prob = [0.0, 0.3, 0.6, 0.9][level]
            for o in self.grid.query_radius(x, y, r):
                if o.is_alive and np.random.random() < prob:
                    o.is_alive = False
            ttl -= 1
            if ttl > 0:
                next_clouds.append((x, y, r, level, ttl))
        self.antibiotic_clouds = next_clouds

    def add_antibiotic_drop(self, x: float, y: float,
                            radius: float, level: int):
        self.antibiotic_clouds.append((x, y, radius, level, 100))

    # ──────────────────────────
    # ДИФФУЗИЯ + РАСПАД
    # ──────────────────────────
    def _diffuse(self, replenish: bool = False):
        self.nutrient_map[:] = (
            (np.roll(self.nutrient_map,  1, 0) +
             np.roll(self.nutrient_map, -1, 0) +
             np.roll(self.nutrient_map,  1, 1) +
             np.roll(self.nutrient_map, -1, 1)) / 4.0
        )
        self.nutrient_map *= 0.997          # ~0.3 % распада

        if replenish:
            self.nutrient_map += 0.002      # лёгкая подпитка

import numpy as np
from .spatial_grid import SpatialHash

class Environment:
    def __init__(self, width=800, height=600, grid_size=60):
        self.width, self.height = width, height
        self.grid_size = grid_size

        self.temperature = 25.0
        self.ph = 7.0
        self.speed_multiplier = 1.0

        self.nutrient_map = np.full((grid_size, grid_size), 6.0, dtype=np.float32)

        self.organisms   = []   # живые и трупы
        self.newborn     = []   # добавляются в конце шага
        self.grid        = SpatialHash(cell_size=20)

        # каждый кортеж: (x, y, radius, level(0-3), ttl)
        self.antibiotic_clouds = []

    # ───────── координаты → индексы без выхода за границы ─────────
    def cell_index(self, x, y) -> tuple[int, int]:
        col = min(int(x / self.width  * self.grid_size),  self.grid_size - 1)
        row = min(int(y / self.height * self.grid_size), self.grid_size - 1)
        return row, col

    # ───────── основной цикл ─────────
    def update(self, steps=1):
        for _ in range(steps):
            self._step()

    def _step(self):
        # (1) spatial-hash
        self.grid.clear()
        for o in self.organisms:
            self.grid.add(o)

        # (2) обновляем организмы
        for o in self.organisms:
            o.update(self)

        # (3) антибиотик
        self._antibiotic_phase()

        # (4) новорождённые
        self.organisms.extend(self.newborn)
        self.newborn.clear()

        # (5) «трупы» остаются 200 тиков
        alive_or_visible = []
        for o in self.organisms:
            if o.is_alive:
                alive_or_visible.append(o)
            else:
                if not o.dead_body:
                    o.dead_body = True
                    o.death_timer = 200
                o.death_timer -= 1
                if o.death_timer > 0:
                    alive_or_visible.append(o)
        self.organisms = alive_or_visible

        # (6) диффузия (раз в 5 тиков)
        if np.random.randint(5) == 0:
            self._diffuse()

    # ───────── антибиотик ─────────
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

    def add_antibiotic_drop(self, x, y, radius, level):
        self.antibiotic_clouds.append((x, y, radius, level, 100))

    # ───────── диффузия ─────────
    def _diffuse(self):
        self.nutrient_map[:] = (
            (np.roll(self.nutrient_map,  1, 0) +
             np.roll(self.nutrient_map, -1, 0) +
             np.roll(self.nutrient_map,  1, 1) +
             np.roll(self.nutrient_map, -1, 1) +
             self.nutrient_map) / 5.0
        )

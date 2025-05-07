# --------------------------------------------------------------
# Организмы с уникальным uid и прежней логикой роста/деления.
# --------------------------------------------------------------
import itertools
import math
import random

_uid_counter = itertools.count()      # глобальный счётчик uid-ов


class Organism:
    # геометрия круглой чашки 500×500 → R = 250
    DISH_R = 250
    DISH_CX = DISH_CY = 250

    def __init__(self, x: float, y: float, profile: dict, size: float = 5.0):
        self.uid = next(_uid_counter)        # ← уникальный id

        self.x, self.y = x, y
        self.size = size
        self.profile = profile

        self.shape = profile["shape"]
        self.color = profile["color"]

        # небольшие стартовые скорости
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)

        self.orientation = random.uniform(0, 360)
        self.is_alive = True
        self.dead_body = False               # для рендера

    # ───── движение с отражением ─────
    def _move(self, env):
        self.x += self.vx
        self.y += self.vy

        dx = self.x - self.DISH_CX
        dy = self.y - self.DISH_CY
        dist2 = dx * dx + dy * dy
        if dist2 > self.DISH_R ** 2:
            dist = dist2 ** 0.5
            nx, ny = dx / dist, dy / dist
            overlap = dist - self.DISH_R
            self.x -= nx * overlap
            self.y -= ny * overlap
            vn = self.vx * nx + self.vy * ny
            self.vx -= 2 * vn * nx
            self.vy -= 2 * vn * ny

    # child classes must override update()
    def update(self, env): ...
# --------------------------------------------------------------
class Bacterium(Organism):
    def __init__(self, x, y, profile):
        super().__init__(x, y, profile, size=5)
        self.division_ticks = int(profile["division_period_min"])
        self.division_size = profile.get("division_size", 8)
        self.max_size = profile.get("max_size", 10)
        self.ticks_since_div = random.randrange(self.division_ticks)

    def update(self, env):
        if not self.is_alive:
            return

        self._nutrition(env)
        self._check_env_limits(env)

        self.ticks_since_div += 1
        if (self.ticks_since_div >= self.division_ticks
                and self.size >= self.division_size):
            self._divide(env)
            self.ticks_since_div = 0

        if random.random() < 0.02:
            ang = math.radians(random.uniform(-15, 15))
            speed = (self.vx ** 2 + self.vy ** 2) ** 0.5 or 4
            self.vx = math.cos(ang) * speed
            self.vy = math.sin(ang) * speed

        self._move(env)

    # helpers ----------------------------------------------------
    def _nutrition(self, env):
        cy, cx = env.cell_index(self.x, self.y)
        food = env.nutrient_map[cy][cx]
        if food > 0:
            eat = min(self.profile["nutrient_consumption"], food)
            env.nutrient_map[cy][cx] -= eat
            self.size = min(self.max_size,
                            self.size + self.profile["growth_rate"])
        else:
            self.is_alive = False

    def _check_env_limits(self, env):
        p = self.profile
        if (env.temperature < p["min_temp"] or env.temperature > p["max_temp"]
                or env.ph < p["min_ph"] or env.ph > p["max_ph"]):
            self.is_alive = False

    def _divide(self, env):
        child_size = self.size / 2
        self.size = child_size
        baby = Bacterium(self.x + random.uniform(-2, 2),
                         self.y + random.uniform(-2, 2),
                         dict(self.profile))
        baby.size = child_size
        baby.vx = random.uniform(-1, 1)
        baby.vy = random.uniform(-1, 1)
        if random.random() < 0.01:
            baby.profile["resistance"] = max(
                0, min(1, baby.profile["resistance"] + random.uniform(-0.05, 0.05))
            )
        env.newborn.append(baby)
# --------------------------------------------------------------
class Fungus(Organism):
    def __init__(self, x, y, profile):
        super().__init__(x, y, profile, size=8)
        self.can_produce_ab = random.random() < profile["antibacterial_ability"]

    def update(self, env):
        if not self.is_alive:
            return

        self._nutrition(env)
        self._check_env_limits(env)

        if self.can_produce_ab:
            self._release_ab(env)

        self.vx *= 0.9
        self.vy *= 0.9
        self._move(env)

    # helpers ----------------------------------------------------
    def _nutrition(self, env):
        cy, cx = env.cell_index(self.x, self.y)
        food = env.nutrient_map[cy][cx]
        if food > 0:
            eat = min(self.profile["nutrient_consumption"], food)
            env.nutrient_map[cy][cx] -= eat
            self.size += self.profile["growth_rate"]
        else:
            self.is_alive = False

    def _check_env_limits(self, env):
        p = self.profile
        if (env.temperature < p["min_temp"] or env.temperature > p["max_temp"]
                or env.ph < p["min_ph"] or env.ph > p["max_ph"]):
            self.is_alive = False

    def _release_ab(self, env):
        r = self.profile["antibacterial_radius"]
        dmg = self.profile["antibacterial_strength"]
        for obj in env.grid.query_radius(self.x, self.y, r):
            if isinstance(obj, Bacterium) and obj.is_alive:
                if random.random() > obj.profile["resistance"]:
                    obj.size -= dmg
                    if obj.size < 1:
                        obj.is_alive = False

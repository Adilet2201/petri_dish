# bacteria_simulation/simulation/organisms.py
import random, math, time

class Organism:
    def __init__(self, x, y, profile, size=5.0):
        self.x, self.y = x, y
        self.size = size
        self.profile = profile
        self.shape = profile["shape"]
        self.color = profile["color"]
        self.vx, self.vy = random.uniform(-4, 4), random.uniform(-4, 4)
        self.orientation = random.uniform(0, 360)
        self.is_alive = True
        self.dead_body = False
        self.death_timer = 0

    # отскок от стен
    def _move(self, env):
        self.x += self.vx
        self.y += self.vy
        if self.x < 0 or self.x > env.width:
            self.vx *= -1; self.x = max(0, min(env.width, self.x))
        if self.y < 0 or self.y > env.height:
            self.vy *= -1; self.y = max(0, min(env.height, self.y))

    def update(self, env):
        pass  # child classes

class Bacterium(Organism):
    def __init__(self, x, y, profile):
        super().__init__(x, y, profile, size=5)
        self.division_ticks = int(profile["division_period_min"] * 60)  # шаг = 1 сек
        self.ticks_since_div = random.randrange(self.division_ticks)

    def update(self, env):
        if not self.is_alive: return
        self._nutrition(env)
        self._check_env_limits(env)
        self.ticks_since_div += 1
        if self.ticks_since_div >= self.division_ticks:
            self._divide(env)
            self.ticks_since_div = 0
        if random.random() < 0.02:
            # маленькие повороты
            ang = math.radians(random.uniform(-15, 15))
            speed = (self.vx ** 2 + self.vy ** 2) ** 0.5 or 4
            self.vx = math.cos(ang) * speed
            self.vy = math.sin(ang) * speed
        self._move(env)

    # --- helpers ---
    def _nutrition(self, env):
        cx, cy = env.cell_index(self.x, self.y)
        food = env.nutrient_map[cy][cx]
        if food > 0:
            eat = min(self.profile["nutrient_consumption"], food)
            env.nutrient_map[cy][cx] -= eat
            self.size += self.profile["growth_rate"]
        else:
            self.size -= 0.02
            if self.size < 1: self.is_alive = False

    def _check_env_limits(self, env):
        p = self.profile
        # температура / pH штраф
        t_pen = max(0, abs(env.temperature - p["optimal_temp"]) * 0.05)
        ph_pen = max(0, abs(env.ph - p["optimal_ph"]) * 0.10)
        self.size -= (t_pen + ph_pen)
        if self.size < 1: self.is_alive = False

    def _divide(self, env):
        child_size = self.size / 2
        self.size = child_size
        baby = Bacterium(self.x + random.uniform(-2, 2),
                         self.y + random.uniform(-2, 2),
                         dict(self.profile))          # копия профиля
        # мутация резистентности
        if random.random() < 0.01:
            baby.profile["resistance"] = max(
                0, min(1, baby.profile["resistance"] + random.uniform(-0.05, 0.05))
            )
        env.newborn.append(baby)

class Fungus(Organism):
    def __init__(self, x, y, profile):
        super().__init__(x, y, profile, size=8)
        self.can_produce_ab = random.random() < profile["antibacterial_ability"]

    def update(self, env):
        if not self.is_alive: return
        self._nutrition(env)
        self._check_env_limits(env)
        if self.can_produce_ab:
            self._release_ab(env)
        # грибы почти не двигаются
        self.vx *= 0.9; self.vy *= 0.9
        self._move(env)

    def _nutrition(self, env):
        cx, cy = env.cell_index(self.x, self.y)
        food = env.nutrient_map[cy][cx]
        if food > 0:
            eat = min(self.profile["nutrient_consumption"], food)
            env.nutrient_map[cy][cx] -= eat
            self.size += self.profile["growth_rate"]
        else:
            self.size -= 0.01
        if self.size < 2: self.is_alive = False

    def _check_env_limits(self, env):
        p = self.profile
        t_pen = max(0, abs(env.temperature - p["optimal_temp"]) * 0.03)
        ph_pen = max(0, abs(env.ph - p["optimal_ph"]) * 0.05)
        self.size -= (t_pen + ph_pen)
        if self.size < 2: self.is_alive = False

    def _release_ab(self, env):
        r = self.profile["antibacterial_radius"]
        dmg = self.profile["antibacterial_strength"]
        for bact in env.grid.query_radius(self.x, self.y, r):
            if isinstance(bact, Bacterium) and bact.is_alive:
                if random.random() > bact.profile["resistance"]:
                    bact.size -= dmg
                    if bact.size < 1: bact.is_alive = False

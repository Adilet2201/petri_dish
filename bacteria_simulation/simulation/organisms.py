import math
import random

class Organism:
    """Базовый класс для любых организмов в чашке Петри."""
    def __init__(self, x, y, profile, size=5.0):
        self.x = x
        self.y = y
        self.size = size
        self.profile = profile
        self.color = profile.get("color", "#000000")
        self.shape = profile.get("shape", "coccus")

        self.is_alive = True
        self.orientation = random.uniform(0, 360)

        # Скорость уменьшили (чтобы не бегали слишком быстро)
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-8, 8)

        self.dividing = False
        self.dying = False

    def move_in_bounds(self, env):
        """Сместить (vx,vy), отразить от краёв."""
        self.x += self.vx
        self.y += self.vy
        # Отражения:
        if self.x < 0:
            self.x = 0
            self.vx *= -1
        if self.x > env.width:
            self.x = env.width
            self.vx *= -1
        if self.y < 0:
            self.y = 0
            self.vy *= -1
        if self.y > env.height:
            self.y = env.height
            self.vy *= -1

    def update(self, env):
        pass


class Bacterium(Organism):
    def __init__(self, x, y, profile, size=5.0):
        super().__init__(x, y, profile, size)
        self.growth_rate = profile.get("growth_rate", 0.1)
        self.max_size_before_division = profile.get("max_size_before_division", 10)
        self.nutrient_consumption = profile.get("nutrient_consumption", 0.05)
        self.resistance = profile.get("resistance", 0.1)

    def update(self, env):
        if not self.is_alive:
            return

        # Питание, рост
        cx, cy = env.get_cell_index(self.x, self.y)
        if cx is None:
            self.is_alive = False
            return
        local_food = env.nutrient_map[cy][cx]
        if local_food > 0:
            consumed = min(self.nutrient_consumption, local_food)
            env.nutrient_map[cy][cx] -= consumed
            gf = env.calc_growth_factor(self.profile, self)
            self.size += self.growth_rate * gf
        else:
            self.size -= 0.01
            if self.size < 1:
                self.is_alive = False

        env.check_temp_ph_limits(self, self.profile)

        # Деление
        if self.size >= self.max_size_before_division and not self.dividing:
            self.dividing = True

        # Немного случайно меняем ориентацию
        if random.random() < 0.02:
            self.orientation += random.uniform(-15, 15)

        # Движение
        self.move_in_bounds(env)
        if self.size < 1:
            self.is_alive = False

    def split_offspring(self):
        # Деление: создаём новую бактерию
        child_size = self.size / 2
        self.size /= 2
        self.dividing = False
        baby = Bacterium(
            self.x + random.uniform(-2, 2),
            self.y + random.uniform(-2, 2),
            self.profile,
            size=child_size
        )
        return baby


class Virus(Organism):
    """Вирус: не растёт, но заражает бактерии при столкновении."""
    def __init__(self, x, y, profile, size=3.0):
        super().__init__(x, y, profile, size)
        self.infect_chance = 0.2
        self.kill_chance = 0.1
        self.resistance = profile.get("resistance", 0.9)

    def update(self, env):
        if not self.is_alive:
            return

        # Движение
        self.move_in_bounds(env)

        # Проверяем столкновения с другими организмами
        for org in env.bacteria:
            if org is not self and org.is_alive:
                dist = ((org.x - self.x)**2 + (org.y - self.y)**2)**0.5
                # Простейшее условие "столкновения", если их радиусы соприкоснулись
                if dist < (org.size + self.size):
                    # Попытка убить
                    if random.random() < self.kill_chance:
                        org.is_alive = False
                    # Или заразить => вирус размножается
                    elif random.random() < self.infect_chance:
                        baby = Virus(self.x, self.y, self.profile, size=self.size)
                        env.new_bacteria.append(baby)


class Fungus(Organism):
    """Гриб: растёт медленно, образует споры при достижении большого размера."""
    def __init__(self, x, y, profile, size=8.0):
        super().__init__(x, y, profile, size)
        self.growth_rate = profile.get("growth_rate", 0.02)
        self.nutrient_consumption = profile.get("nutrient_consumption", 0.1)
        self.max_size_before_division = profile.get("max_size_before_division", 20)

    def update(self, env):
        if not self.is_alive:
            return

        cx, cy = env.get_cell_index(self.x, self.y)
        if cx is None:
            self.is_alive = False
            return
        local_food = env.nutrient_map[cy][cx]
        if local_food > 0:
            consumed = min(self.nutrient_consumption, local_food)
            env.nutrient_map[cy][cx] -= consumed
            gf = env.calc_growth_factor(self.profile, self)
            self.size += self.growth_rate * gf
        else:
            self.size -= 0.005
            if self.size < 2:
                self.is_alive = False

        env.check_temp_ph_limits(self, self.profile)

        # Если гриб достиг max_size => выпустит споры
        if self.size >= self.max_size_before_division and not self.dividing:
            self.dividing = True

        # Грибы почти не двигаются
        self.vx *= 0.9
        self.vy *= 0.9
        self.move_in_bounds(env)

    def release_spores(self):
        spore_count = random.randint(2, 3)
        child_size = self.size / (spore_count+1)
        self.size *= 0.5
        self.dividing = False

        spores = []
        for _ in range(spore_count):
            sx = self.x + random.uniform(-3, 3)
            sy = self.y + random.uniform(-3, 3)
            s = Fungus(sx, sy, self.profile, size=child_size)
            spores.append(s)
        return spores

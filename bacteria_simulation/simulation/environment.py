import random
from .organisms import Bacterium, Virus, Fungus

class Environment:
    def __init__(self, width=600, height=600, grid_size=60):
        self.width = width
        self.height = height
        self.grid_size = grid_size

        self.temperature = 25.0
        self.ph = 7.0
        self.antibiotic_strength = 1.0

        self.nutrient_map = [[5.0 for _ in range(grid_size)] for _ in range(grid_size)]

        # Храним всех организмов (бактерии, вирусы, грибы) в одном списке
        self.bacteria = []
        self.new_bacteria = []

        self.simulation_time = 0
        self.paused = False

    def update(self, steps=1):
        for _ in range(steps):
            self.simulation_time += 1

            # Обновляем всех
            for org in self.bacteria:
                org.update(self)
                # Если организм делится
                if org.is_alive and org.dividing:
                    if org.shape in ("coccus","rod","spirillum"):
                        # Это бактерия
                        child = org.split_offspring()
                        self.new_bacteria.append(child)
                    elif org.shape == "fungus":
                        # Выделяет споры
                        spores = org.release_spores()
                        self.new_bacteria.extend(spores)
                    org.dividing = False

            # Удаляем мёртвых
            self.bacteria = [o for o in self.bacteria if o.is_alive]
            # Добавляем новорождённых
            self.bacteria.extend(self.new_bacteria)
            self.new_bacteria.clear()

            # Диффузия
            self.diffuse_nutrients()

    def diffuse_nutrients(self):
        new_map = [[0.0]*self.grid_size for _ in range(self.grid_size)]
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                total, count = 0.0, 0
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        nx = x+dx
                        ny = y+dy
                        if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                            total += self.nutrient_map[ny][nx]
                            count += 1
                new_map[y][x] = total / count
        self.nutrient_map = new_map

    def get_cell_index(self, px, py):
        if not (0<=px<=self.width and 0<=py<=self.height):
            return (None, None)
        cell_x = int(px/(self.width/self.grid_size))
        cell_y = int(py/(self.height/self.grid_size))
        cell_x = min(cell_x, self.grid_size-1)
        cell_y = min(cell_y, self.grid_size-1)
        return (cell_x, cell_y)

    def calc_growth_factor(self, profile, org):
        temp_opt = profile["optimal_temp"]
        diff_t = abs(self.temperature - temp_opt)
        ft = max(0.1, 1.0 - 0.05*diff_t)

        ph_opt = profile["optimal_ph"]
        diff_p = abs(self.ph - ph_opt)
        fp = max(0.1, 1.0 - 0.1*diff_p)

        return ft * fp

    def check_temp_ph_limits(self, organism, profile):
        if self.temperature < profile["min_temp"]:
            d = profile["min_temp"] - self.temperature
            organism.size -= 0.02*d
        if self.temperature > profile["max_temp"]:
            d = self.temperature - profile["max_temp"]
            organism.size -= 0.02*d

        if self.ph < profile["min_ph"]:
            dp = profile["min_ph"] - self.ph
            organism.size -= 0.02*dp
        if self.ph > profile["max_ph"]:
            dp = self.ph - profile["max_ph"]
            organism.size -= 0.02*dp

        if organism.size<1:
            organism.is_alive = False

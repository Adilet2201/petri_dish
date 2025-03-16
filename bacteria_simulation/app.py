import threading
import time
import random
import math

from flask import Flask, render_template, request, jsonify

# ------------------------------------
# ПАРАМЕТРЫ ПОЛЯ
# ------------------------------------
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 600

# Сетка для питательных веществ: 60×60 => каждая клетка ~ 10×10 пикселей
GRID_SIZE = 60

app = Flask(__name__)

# ------------------------------------
# ПРОФИЛИ ВИДОВ (Growth / Consumption / Цвет / Форма и т.п.)
# Добавили "min_temp", "max_temp", "resistance"
# ------------------------------------
SPECIES_PROFILES = {
    "Coccus": {
        "color": "#FF0000",
        "growth_rate": 0.1,
        "max_size_before_division": 10,
        "nutrient_consumption": 0.05,
        "shape": "coccus",
        "min_temp": 0,     # ниже 0 °C – гибнет
        "max_temp": 40,    # выше 40 °C – гибнет
        "resistance": 0.1  # Низкая устойчивость к антибиотику
    },
    "Rod": {
        "color": "#00AAFF",
        "growth_rate": 0.15,
        "max_size_before_division": 12,
        "nutrient_consumption": 0.07,
        "shape": "rod",
        "min_temp": 5,
        "max_temp": 45,
        "resistance": 0.5  # Средняя устойчивость
    },
    "Spirillum": {
        "color": "#55FF55",
        "growth_rate": 0.08,
        "max_size_before_division": 14,
        "nutrient_consumption": 0.06,
        "shape": "spirillum",
        "min_temp": 10,
        "max_temp": 50,
        "resistance": 0.8  # Достаточно устойчивая
    }
}

# ------------------------------------
# КЛАСС БАКТЕРИИ
# ------------------------------------
class Bacterium:
    def __init__(self, x, y, species="Coccus", size=5.0):
        self.x = x
        self.y = y
        self.size = size
        self.species = species

        # Загружаем параметры из профиля
        profile = SPECIES_PROFILES.get(species, SPECIES_PROFILES["Coccus"])
        self.color = profile["color"]
        self.growth_rate = profile["growth_rate"]
        self.max_size_before_division = profile["max_size_before_division"]
        self.nutrient_consumption = profile["nutrient_consumption"]
        self.shape = profile["shape"]
        self.min_temp = profile["min_temp"]
        self.max_temp = profile["max_temp"]
        self.resistance = profile["resistance"]

        self.is_alive = True
        self.orientation = random.uniform(0, 2*math.pi)  # угол "носом"

    def update(self, environment):
        """Обновление состояния за один тик."""
        if not self.is_alive:
            return

        # 1) Потребление пит. веществ
        cell_x = int(self.x / (CANVAS_WIDTH / GRID_SIZE))
        cell_y = int(self.y / (CANVAS_HEIGHT / GRID_SIZE))
        if 0 <= cell_x < GRID_SIZE and 0 <= cell_y < GRID_SIZE:
            local_nutrients = environment.nutrient_map[cell_y][cell_x]
            if local_nutrients > 0:
                consumed = min(self.nutrient_consumption, local_nutrients)
                environment.nutrient_map[cell_y][cell_x] -= consumed
                self.size += self.growth_rate
            else:
                # Нет еды => медленно уменьшаемся
                self.size -= 0.02
                if self.size < 1:
                    self.is_alive = False
        else:
            # Вышли за границу
            self.is_alive = False

        # 2) Температура
        # Если выходим за min_temp / max_temp, бактерия начинает "чахнуть" и может умереть
        if environment.temperature < self.min_temp:
            diff = self.min_temp - environment.temperature
            # чем больше diff, тем сильнее падение
            self.size -= 0.02 * diff
            if self.size < 1:
                self.is_alive = False
        elif environment.temperature > self.max_temp:
            diff = environment.temperature - self.max_temp
            self.size -= 0.02 * diff
            if self.size < 1:
                self.is_alive = False
        # Если хотим учесть "оптимальную" температуру (например, midpoint = (min+max)/2),
        # можно еще варьировать рост. (Сейчас для упрощения это пропустим.)

        # 3) Деление
        if self.size >= self.max_size_before_division:
            child = Bacterium(
                x=self.x + random.uniform(-2, 2),
                y=self.y + random.uniform(-2, 2),
                species=self.species,
                size=self.size / 2
            )
            self.size /= 2
            environment.new_bacteria.append(child)

        # 4) Движение (хемотаксис)
        self.chemotaxis(environment)

    def chemotaxis(self, environment):
        """Примитивный поиск участков с большим содержанием еды."""
        step_size = 1.5
        cx = int(self.x / (CANVAS_WIDTH / GRID_SIZE))
        cy = int(self.y / (CANVAS_HEIGHT / GRID_SIZE))

        best_val = 0
        best_dx, best_dy = 0, 0
        radius_cells = 1  # ищем в окрестности 3x3

        for dy in range(-radius_cells, radius_cells+1):
            for dx in range(-radius_cells, radius_cells+1):
                nx = cx + dx
                ny = cy + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    val = environment.nutrient_map[ny][nx]
                    if val > best_val:
                        best_val = val
                        best_dx = dx
                        best_dy = dy

        if best_val > 0:
            angle = math.atan2(best_dy, best_dx)
            self.orientation = angle
        else:
            # случайное блуждание
            if random.random() < 0.01:
                self.orientation += random.uniform(-math.pi/2, math.pi/2)

        # Двигаемся
        self.x += step_size * math.cos(self.orientation)
        self.y += step_size * math.sin(self.orientation)

        # Границы
        if self.x < 0: 
            self.x = 0
        if self.x > CANVAS_WIDTH:
            self.x = CANVAS_WIDTH
        if self.y < 0:
            self.y = 0
        if self.y > CANVAS_HEIGHT:
            self.y = CANVAS_HEIGHT


# ------------------------------------
# КЛАСС ОКРУЖЕНИЯ
# ------------------------------------
class Environment:
    def __init__(self):
        # 2D‑карта пит. веществ, по умолчанию 5
        self.nutrient_map = [[5 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.temperature = 25.0
        self.bacteria = []
        self.new_bacteria = []
        self.simulation_time = 0

        # Можно добавить "strength" антибиотика, если хотим
        self.antibiotic_strength = 1.0

    def update(self):
        self.simulation_time += 1

        # Обновляем все бактерии
        for b in self.bacteria:
            b.update(self)

        # Убираем мёртвых
        self.bacteria = [b for b in self.bacteria if b.is_alive]

        # Добавляем новорожденных
        self.bacteria.extend(self.new_bacteria)
        self.new_bacteria.clear()

        # Диффузия (можно отключить или упростить)
        self.diffuse_nutrients()

    def diffuse_nutrients(self):
        """
        Простейшее размывание питательных веществ.
        """
        new_map = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                total = 0
                count = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        nx = x + dx
                        ny = y + dy
                        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                            total += self.nutrient_map[ny][nx]
                            count += 1
                new_map[y][x] = total / count
        self.nutrient_map = new_map

    def apply_antibiotic(self, x, y, radius):
        """
        Применение антибиотика в радиусе. 
        Учитываем `resistance` бактерии и self.antibiotic_strength.
        """
        killed = 0
        for b in self.bacteria:
            dist = math.hypot(b.x - x, b.y - y)
            if dist <= radius:
                # Проверяем, умирает ли бактерия
                # Пример простейшей формулы: 
                # chance_to_die = antibiotic_strength - resistance 
                # (но не меньше 0 и не больше 1)
                chance_to_die = self.antibiotic_strength - b.resistance
                if chance_to_die < 0:
                    chance_to_die = 0
                if chance_to_die > 1:
                    chance_to_die = 1

                # С вероятностью chance_to_die бактерия умрёт
                if random.random() < chance_to_die:
                    b.is_alive = False
                    killed += 1
                else:
                    # Иначе можем частично повредить — например, снизить размер
                    b.size *= 0.8
        return killed


# ------------------------------------
# ГЛОБАЛЬНОЕ ОКРУЖЕНИЕ
# ------------------------------------
environment = Environment()

# Для примера – по 2 штуки каждого вида
for sp in ["Coccus", "Rod", "Spirillum"]:
    for _ in range(2):
        bx = random.uniform(250, 350)
        by = random.uniform(250, 350)
        environment.bacteria.append(Bacterium(x=bx, y=by, species=sp))

# ------------------------------------
# ПОТОК СИМУЛЯЦИИ
# ------------------------------------
def simulation_loop():
    while True:
        environment.update()
        time.sleep(0.1)  # 10 раз/сек

thread = threading.Thread(target=simulation_loop, daemon=True)
thread.start()

# ------------------------------------
# МАРШРУТЫ FLASK
# ------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/state", methods=["GET"])
def get_state():
    # Список бактерий
    bacteria_data = []
    for b in environment.bacteria:
        bacteria_data.append({
            "x": b.x,
            "y": b.y,
            "size": b.size,
            "color": b.color,
            "shape": b.shape,
            "orientation": b.orientation
        })

    data = {
        "nutrientMap": environment.nutrient_map,
        "temperature": environment.temperature,
        "bacteria": bacteria_data,
        "simulationTime": environment.simulation_time,
        "antibioticStrength": environment.antibiotic_strength
    }
    return jsonify(data)

@app.route("/update_environment", methods=["POST"])
def update_environment():
    data = request.json
    temp = data.get("temperature")
    if temp is not None:
        environment.temperature = float(temp)

    # Если хотим менять "strength" антибиотика
    strength = data.get("antibioticStrength")
    if strength is not None:
        environment.antibiotic_strength = float(strength)

    return jsonify({"message": "Environment updated."})

@app.route("/add_bacterium", methods=["POST"])
def add_bacterium():
    data = request.json
    x = data.get("x", 300)
    y = data.get("y", 300)
    species = data.get("species", "Coccus")

    new_bac = Bacterium(x, y, species=species)
    environment.bacteria.append(new_bac)
    return jsonify({"message": f"Added {species} at ({x}, {y})."})

@app.route("/apply_antibiotic", methods=["POST"])
def apply_antibiotic():
    data = request.json
    x = data.get("x", 300)
    y = data.get("y", 300)
    radius = data.get("radius", 50)

    killed = environment.apply_antibiotic(x, y, radius)
    return jsonify({"message": f"Antibiotic used at ({x}, {y}), radius={radius}, killed={killed}."})

if __name__ == "__main__":
    app.run(debug=True)

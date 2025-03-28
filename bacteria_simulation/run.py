import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
import random

# Внутренние импорты
from .simulation.environment import Environment
from .simulation.updater import SimulationUpdater
from .webapp.routes import routes_bp
from .webapp.socketio_events import init_socketio
from .profiles import SPECIES_PROFILES

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "secret!"

    # Создаём окружение симуляции (Petri dish)
    env = Environment(width=800, height=600, grid_size=60)

    # Заполняем окружение начальными организмами (например, 15 бактерий, 3 вируса, 2 гриба)
    from .simulation.organisms import Bacterium, Virus, Fungus
    for _ in range(15):
        x = random.uniform(0, env.width)
        y = random.uniform(0, env.height)
        # Случайно выберем бактерию из профилей "Coccus"/"Rod"/"Spirillum"
        sp_key = random.choice(["Coccus","Rod","Spirillum"])
        profile = SPECIES_PROFILES[sp_key]
        env.bacteria.append(Bacterium(x, y, profile))

    # Добавим чуть вирусов и грибов
    for _ in range(3):
        x = random.uniform(0, env.width)
        y = random.uniform(0, env.height)
        virus_profile = SPECIES_PROFILES["Virus"]
        env.bacteria.append(Virus(x, y, virus_profile))

    for _ in range(2):
        x = random.uniform(0, env.width)
        y = random.uniform(0, env.height)
        fungus_profile = SPECIES_PROFILES["Fungus"]
        env.bacteria.append(Fungus(x, y, fungus_profile))

    # Сохраняем окружение и профили в конфигурации
    app.config["env"] = env
    app.config["species_profiles"] = SPECIES_PROFILES

    # Регистрируем Blueprint с маршрутами
    app.register_blueprint(routes_bp)
    return app, env

if __name__ == "__main__":
    app, env = create_app()

    socketio = SocketIO(app, async_mode="eventlet")

    # Создаём обновляющий поток, который каждые 0.2 с вызывает env.update и шлёт state_update
    updater = SimulationUpdater(env, socketio, interval=0.2)
    updater.start()

    # Инициализируем обработчики Socket.IO (pause/play и т.д.)
    init_socketio(socketio, updater)

    socketio.run(app, debug=True, use_reloader=False)

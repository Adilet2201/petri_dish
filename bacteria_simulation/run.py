# Ваш главный модуль (например app.py)

import eventlet, random
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
from bacteria_simulation.simulation.environment import Environment
from bacteria_simulation.simulation.organisms  import Bacterium, Fungus
from bacteria_simulation.simulation.updater    import SimulationUpdater
from bacteria_simulation.profiles              import SPECIES_PROFILES
from bacteria_simulation.webapp.routes         import bp
from bacteria_simulation.webapp.socketio_events import init_events

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "secret"

    env = Environment(width=500, height=500)

    # Сажаем по 5 особей каждого вида в profiles
    for species, prof in SPECIES_PROFILES.items():
        for _ in range(5):
            x, y = random.uniform(0, env.width), random.uniform(0, env.height)
            if prof["shape"] == "fungus":
                env.organisms.append(Fungus(x, y, prof))
            else:
                env.organisms.append(Bacterium(x, y, prof))

    app.config["env"]      = env
    app.config["profiles"] = SPECIES_PROFILES
    app.register_blueprint(bp)
    return app, env

app, env = create_app()
io = SocketIO(app, async_mode="eventlet")
app.config["socketio"] = io

updater = SimulationUpdater(env, io, interval=0.05)
io.start_background_task(updater.run)

init_events(io, updater)

if __name__ == "__main__":
    io.run(app, host="0.0.0.0", port=5050, debug=True, use_reloader=False)

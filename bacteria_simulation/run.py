import eventlet, random
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
from .simulation.environment import Environment
from .simulation.organisms  import Bacterium, Fungus
from .simulation.updater    import SimulationUpdater
from .profiles              import SPECIES_PROFILES
from .webapp.routes         import bp
from .webapp.socketio_events import init_events


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "secret"

    env = Environment(width=500, height=500)   # канва 500×500

    # стартовые бактерии + грибы
    for _ in range(20):
        x, y = random.uniform(0, env.width), random.uniform(0, env.height)
        kind = random.choice(["Coccus", "Rod", "Spirillum"])
        env.organisms.append(Bacterium(x, y, SPECIES_PROFILES[kind]))
    for _ in range(3):
        x, y = random.uniform(0, env.width), random.uniform(0, env.height)
        env.organisms.append(Fungus(x, y, SPECIES_PROFILES["Fungus"]))

    app.config["env"] = env
    app.config["profiles"] = SPECIES_PROFILES
    app.register_blueprint(bp)
    return app, env


# ───────── Socket.IO ─────────
app, env = create_app()
io = SocketIO(app, async_mode="eventlet")
app.config["socketio"] = io           # доступ из роутов

updater = SimulationUpdater(env, io, interval=0.05)   # 20 FPS
io.start_background_task(updater.run)

init_events(io, updater)

if __name__ == "__main__":
    io.run(app, host="0.0.0.0", port=5050,
           debug=True, use_reloader=False)

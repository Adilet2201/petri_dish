# bacteria_simulation/simulation/updater.py
import time

class SimulationUpdater:
    def __init__(self, env, socketio, interval=0.2):
        self.env = env
        self.io = socketio
        self.interval = interval

    def run(self):
        while True:
            self.env.update(int(self.env.speed_multiplier))
            self.io.emit("state_update", _pack(self.env))
            time.sleep(self.interval / self.env.speed_multiplier)

def _pack(env):
    return {
        "simulationTime": int(time.time()),
        "temperature": env.temperature,
        "ph": env.ph,
        "organisms": [
            {
                "x": o.x, "y": o.y, "size": o.size,
                "vx": o.vx, "vy": o.vy,
                "orientation": o.orientation,
                "color": o.color,
                "shape": o.shape,
                "dead": o.dead_body and not o.is_alive
            }
            for o in env.organisms
        ]
    }

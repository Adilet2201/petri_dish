import time


class SimulationUpdater:
    """
    20 кадров/с (interval = 0.05). Каждая итерация = один суб-тик,
    поэтому одна биоминутка по-прежнему занимает 1 реальную секунду.
    """

    def __init__(self, env, socketio, interval: float = 0.05):
        self.env = env
        self.io = socketio
        self.interval = interval          # 0.05 с ⇒ 20 FPS

    def run(self):
        while True:
            if self.env.speed_multiplier <= 0.0:
                time.sleep(self.interval)
                continue

            # один суб-тик
            self.env.update(steps=1)

            # отправляем «снимок» фронту
            self.io.emit("state_update", _pack(self.env))

            time.sleep(self.interval)


# ───────────────────────────────────────────────
def _pack(env):
    """Минимальный snapshot состояния для фронтенда."""
    return {
        "simulationTime": int(time.time()),
        "temperature": env.temperature,
        "ph": env.ph,
        "organisms": [
            {
                "uid": o.uid,
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

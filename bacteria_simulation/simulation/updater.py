import time

# 1 реальная секунда = 1 сим-мин при speed_multiplier = 1
REAL_SEC_PER_SIM_MIN = 1.0
# теперь шлём state_update ~60 раз в секунду
FRAME_INTERVAL        = 1.0 / 60

class SimulationUpdater:
    def __init__(self, env, socketio, interval: float = FRAME_INTERVAL):
        self.env      = env
        self.io       = socketio
        self.interval = interval
        self.accum    = 0.0    # накопленное реальное время

    def run(self):
        while True:
            if self.env.speed_multiplier <= 0.0:
                # на паузе — не считаем сим-время, но всё равно шлём кадр
                time.sleep(self.interval)
                self.io.emit("state_update", _pack(self.env))
                continue

            # накапливаем реальные секунды, умноженные на мультипликатор
            self.accum += self.interval * self.env.speed_multiplier

            # выполняем столько биотиков, сколько накопилось «минут»
            while self.accum >= REAL_SEC_PER_SIM_MIN:
                self.env.update(steps=1)
                self.accum -= REAL_SEC_PER_SIM_MIN

            # шлём новый кадр клиентам
            self.io.emit("state_update", _pack(self.env))
            time.sleep(self.interval)


def _pack(env):
    """Сериализует состояние для фронтенда."""
    return {
        "simulationTime": int(time.time()),
        "temperature":    env.temperature,
        "ph":             env.ph,
        "organisms": [
            {
                "uid":   o.uid,
                "x":     o.x, "y": o.y, "size": o.size,
                "vx":    o.vx, "vy": o.vy,
                "orientation": o.orientation,
                "color": o.color,
                "shape": o.shape,
                "dead":  o.dead_body and not o.is_alive
            }
            for o in env.organisms
        ]
    }

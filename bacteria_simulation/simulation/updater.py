import time
import threading

class SimulationUpdater:
    def __init__(self, env, socketio, interval=0.2):
        self.env = env
        self.socketio = socketio
        self.interval = interval
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def run(self):
        while True:
            if not self.env.paused:
                self.env.update(steps=1)
                # Формируем пакет
                state_data = {
                    "simulationTime": self.env.simulation_time,
                    "temperature": self.env.temperature,
                    "ph": self.env.ph,
                    "organisms": []
                }
                # Записываем данные обо всех организмах
                for org in self.env.bacteria:
                    state_data["organisms"].append({
                        "x": org.x,
                        "y": org.y,
                        "vx": org.vx,
                        "vy": org.vy,
                        "size": org.size,
                        "orientation": org.orientation,
                        "color": org.color,
                        "shape": org.shape,
                        "dividing": org.dividing,
                        "dying": org.dying
                    })
                self.socketio.emit("state_update", state_data)
            time.sleep(self.interval)

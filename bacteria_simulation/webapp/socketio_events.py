from flask_socketio import emit
from ..simulation.analysis import analyze_population

def init_events(socketio, updater):
    @socketio.on("pause")   # только пауза картинка
    def pause(): updater.env.speed_multiplier = 0.0
    @socketio.on("play")
    def play():  updater.env.speed_multiplier = 1.0
    @socketio.on("get_analysis")
    def analysis():
        emit("analysis_data", analyze_population(updater.env))

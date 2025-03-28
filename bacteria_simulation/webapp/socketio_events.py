from flask_socketio import SocketIO, emit
from ..simulation.analysis import analyze_population

socketio = None
updater = None

def init_socketio(sio, sim_updater):
    global socketio, updater
    socketio = sio
    updater = sim_updater

    @socketio.on("pause")
    def pause_simulation():
        updater.env.paused = True
        emit("paused", {"status": "paused"}, broadcast=True)

    @socketio.on("play")
    def play_simulation():
        updater.env.paused = False
        emit("playing", {"status": "playing"}, broadcast=True)

    @socketio.on("get_analysis")
    def get_analysis():
        env = updater.env
        results = analyze_population(env)
        emit("analysis_data", results)

from flask import Blueprint, request, jsonify, current_app, render_template
from ..simulation.updater import _pack

bp = Blueprint("routes", __name__)


# ───────── HTML ─────────
@bp.route("/")
def index():
    return render_template("index.html")


# ───────── изменение среды ─────────
@bp.route("/update_environment", methods=["POST"])
def update_environment():
    env = current_app.config["env"]
    d   = request.json or {}
    if "temperature"     in d: env.temperature      = float(d["temperature"])
    if "ph"              in d: env.ph               = float(d["ph"])
    if "speedMultiplier" in d: env.speed_multiplier = float(d["speedMultiplier"])
    return jsonify(ok=True)


# ───────── добавление организма ─────────
@bp.route("/add_organism", methods=["POST"])
def add_organism():
    env  = current_app.config["env"]
    data = request.json or {}
    x, y = float(data["x"]), float(data["y"])
    sp   = data.get("species", "Coccus")

    from ..simulation.organisms import Bacterium, Fungus
    prof = current_app.config["profiles"][sp]
    env.organisms.append(
        Fungus(x, y, prof) if prof["shape"] == "fungus" else Bacterium(x, y, prof)
    )

    # мгновенный снапшот
    socketio = current_app.config["socketio"]
    socketio.emit("state_update", _pack(env))
    return jsonify(added=sp)


# alias для старого энд-пойнта
@bp.route("/add_bacterium", methods=["POST"])
def alias_add_bacterium():
    return add_organism()


# ───────── антибиотик ─────────
@bp.route("/apply_antibiotic", methods=["POST"])
def antibiotic():
    env = current_app.config["env"]
    d   = request.json or {}
    env.add_antibiotic_drop(float(d["x"]), float(d["y"]),
                            float(d.get("radius", 50)),
                            int  (d.get("level", 1)))
    return jsonify(ok=True)


# ───────── CLEAR ─────────
@bp.route("/clear_organisms", methods=["POST"])
def clear_organisms():
    env = current_app.config["env"]
    env.organisms.clear()
    env.newborn.clear()

    socketio = current_app.config["socketio"]
    socketio.emit("state_update", _pack(env))
    return jsonify(cleared=True)

from flask import Blueprint, request, jsonify, current_app, render_template
from ..simulation.updater import _pack      # для мгновенного state_update

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

    # координаты клика
    x, y = float(data["x"]), float(data["y"])
    sp   = data.get("species", "Coccus")

    # гарантируем, что точка внутри круга R = 250
    cx = cy = 250
    r2 = 250 ** 2
    if (x - cx) ** 2 + (y - cy) ** 2 > r2:
        dx, dy = x - cx, y - cy
        dist   = (dx * dx + dy * dy) ** 0.5
        x = cx + dx / dist * 250
        y = cy + dy / dist * 250

    # создаём организм
    from ..simulation.organisms import Bacterium, Fungus
    prof = current_app.config["profiles"][sp]

    env.organisms.append(
        Fungus(x, y, prof) if prof["shape"] == "fungus"
        else Bacterium(x, y, prof)
    )

    # сразу шлём клиентам новый state_update,
    # даже если симуляция стоит на паузе
    socketio = current_app.config["socketio"]
    socketio.emit("state_update", _pack(env))

    return jsonify(added=sp)


# --- alias для старого фронта ---
@bp.route("/add_bacterium", methods=["POST"])
def alias_add_bacterium():
    return add_organism()


# ───────── антибиотик ─────────
@bp.route("/apply_antibiotic", methods=["POST"])
def antibiotic():
    env = current_app.config["env"]
    d   = request.json or {}

    env.add_antibiotic_drop(
        float(d["x"]), float(d["y"]),
        float(d.get("radius", 50)),
        int  (d.get("level", 1))
    )
    return jsonify(ok=True)

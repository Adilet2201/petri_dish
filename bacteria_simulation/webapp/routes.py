from flask import Blueprint, request, jsonify, current_app, render_template

bp = Blueprint("routes", __name__)

# ───────── HTML ─────────
@bp.route("/")
def index():
    return render_template("index.html")

# ───────── изменение среды ─────────
@bp.route("/update_environment", methods=["POST"])
def update_environment():
    env = current_app.config["env"]
    d = request.json or {}
    if "temperature"      in d: env.temperature      = float(d["temperature"])
    if "ph"               in d: env.ph               = float(d["ph"])
    if "speedMultiplier"  in d: env.speed_multiplier = float(d["speedMultiplier"])
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
    env.organisms.append(Fungus(x, y, prof) if prof["shape"] == "fungus"
                         else Bacterium(x, y, prof))
    return jsonify(added=sp)

# --- alias, чтобы СТАРЫЙ фронт (/add_bacterium) тоже работал ---
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
                            int(d.get("level", 1)))
    return jsonify(ok=True)

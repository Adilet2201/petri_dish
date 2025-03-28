from flask import Blueprint, request, jsonify, render_template, current_app
import random

routes_bp = Blueprint('routes_bp', __name__)

@routes_bp.route("/")
def index():
    return render_template("index.html")

@routes_bp.route("/update_environment", methods=["POST"])
def update_environment():
    data = request.json
    env = current_app.config["env"]

    temp = data.get("temperature")
    if temp is not None:
        env.temperature = float(temp)

    ph_val = data.get("ph")
    if ph_val is not None:
        env.ph = float(ph_val)

    ab_val = data.get("antibioticStrength")
    if ab_val is not None:
        env.antibiotic_strength = float(ab_val)

    return jsonify({"message": "Environment updated."})

@routes_bp.route("/add_bacterium", methods=["POST"])
def add_bacterium():
    data = request.json
    x = data.get("x", 400)
    y = data.get("y", 300)
    sp_key = data.get("species", "Coccus")

    env = current_app.config["env"]
    from ..simulation.organisms import Bacterium, Virus, Fungus
    sp_profile = current_app.config["species_profiles"].get(sp_key)
    if not sp_profile:
        return jsonify({"error": "Unknown species"}), 400

    shape = sp_profile.get("shape", "coccus")
    if shape in ("coccus","rod","spirillum"):
        env.bacteria.append(Bacterium(x,y, sp_profile))
    elif shape=="virus":
        env.bacteria.append(Virus(x,y, sp_profile))
    elif shape=="fungus":
        env.bacteria.append(Fungus(x,y, sp_profile))

    return jsonify({"message": f"Added {sp_key} at {x},{y}"})

@routes_bp.route("/apply_antibiotic", methods=["POST"])
def apply_antibiotic():
    data = request.json
    x = data.get("x", 400)
    y = data.get("y", 300)
    radius = data.get("radius", 50)

    env = current_app.config["env"]
    killed = 0
    for o in env.bacteria:
        dist = ((o.x - x)**2 + (o.y - y)**2)**0.5
        if dist<=radius:
            chance = env.antibiotic_strength - o.profile.get("resistance",0.1)
            chance = max(0, min(chance, 1))
            if random.random()<chance:
                # Вместо мгновенной смерти — помечаем dying, визуально затухаем
                o.dying = True
                o.is_alive = False
                killed += 1

    return jsonify({"message": f"killed={killed} by antibiotic."})

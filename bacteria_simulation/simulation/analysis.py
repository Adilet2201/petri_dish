# bacteria_simulation/simulation/analysis.py
from .organisms import Bacterium, Fungus

def analyze_population(env):
    total = len(env.organisms)
    bac = sum(isinstance(o, Bacterium) and o.is_alive for o in env.organisms)
    fun = sum(isinstance(o, Fungus)    and o.is_alive for o in env.organisms)
    avg_size = (sum(o.size for o in env.organisms if o.is_alive) / bac) if bac else 0
    return {
        "count": total,
        "bacteria_count": bac,
        "fungus_count": fun,
        "avg_size": round(avg_size, 2)
    }

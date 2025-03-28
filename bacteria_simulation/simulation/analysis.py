def analyze_population(env):
    """
    Возвращает сводную информацию:
     - Общее число организмов
     - Сколько бактерий, вирусов, грибов
     - Средний размер
    """
    organisms = env.bacteria
    count = len(organisms)
    if count == 0:
        return {
            "count": 0,
            "bacteria_count": 0,
            "virus_count": 0,
            "fungus_count": 0,
            "avg_size": 0
        }
    bac_count = 0
    vir_count = 0
    fun_count = 0
    total_size = 0.0
    for o in organisms:
        total_size += o.size
        if o.shape in ("coccus", "rod", "spirillum"):
            bac_count += 1
        elif o.shape == "virus":
            vir_count += 1
        elif o.shape == "fungus":
            fun_count += 1

    return {
        "count": count,
        "bacteria_count": bac_count,
        "virus_count": vir_count,
        "fungus_count": fun_count,
        "avg_size": total_size / count
    }

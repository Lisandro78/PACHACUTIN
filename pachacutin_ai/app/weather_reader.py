import random

def get_weather():
    """Genera clima simulado para Callao en invierno."""
    temperatura = random.uniform(14, 19)  # °C
    humedad_aire = random.uniform(80, 100)  # %

    return {
        "temperatura": round(temperatura, 1),
        "humedad_aire": round(humedad_aire, 1)
    }

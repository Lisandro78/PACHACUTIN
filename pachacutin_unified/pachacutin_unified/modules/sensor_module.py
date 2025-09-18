import random
import time

class SensorModule:
    def __init__(self):
        self.data = {}

    def update_from_serial(self, data: dict):
        # Se llama cuando llega JSON del Arduino por serial
        if not isinstance(data, dict):
            return
        if "soil_moisture" in data:
            self.data["soil_moisture"] = data["soil_moisture"]
        if "soil_type" in data:
            # si algún proceso externo pone soil_type, lo guardamos
            self.data["soil_type"] = data["soil_type"]
        if "temperature" in data:
            self.data["temperature"] = data["temperature"]
        if "air_humidity" in data:
            self.data["air_humidity"] = data["air_humidity"]

    def get_state(self):
        # Fallbacks SIEMPRE activos si no hay dato real
        now_ms = int(time.time() * 1000)
        return {
            "soil_moisture": self.data.get("soil_moisture", "not found"),
            "temperature": self.data.get("temperature", round(random.uniform(16.0, 17.0), 1)),
            "air_humidity": self.data.get("air_humidity", random.randint(80, 85)),
            "soil_type": self.data.get("soil_type", "not found"),
            "ts": str(now_ms),
        }

import random
import time

# Importar clasificador de suelo
try:
    from soil_classifier.classify import SoilClassifier
    SOIL_AVAILABLE = True
except ImportError:
    SOIL_AVAILABLE = False
    SoilClassifier = None


class SensorModule:
    def __init__(self):
        # Diccionario para guardar los últimos valores de sensores
        self.data = {}

        # Inicializar clasificador de suelo (si existe)
        self.soil_classifier = SoilClassifier() if SOIL_AVAILABLE else None

    def update_from_serial(self, data: dict):
        """
        Recibe un diccionario desde el Arduino (JSON) y actualiza estado.
        """
        if not isinstance(data, dict):
            return

        if "soil_moisture" in data:
            self.data["soil_moisture"] = data["soil_moisture"]

        if "temperature" in data:
            self.data["temperature"] = data["temperature"]

        if "air_humidity" in data:
            self.data["air_humidity"] = data["air_humidity"]

        if "soil_type" in data:
            # Arduino puede mandar soil_type directo
            self.data["soil_type"] = data["soil_type"]

    def run_soil_classifier(self, image_path=None):
        """
        Corre el clasificador de suelo y actualiza el tipo en self.data.
        image_path: ruta opcional de imagen a clasificar.
        """
        if self.soil_classifier is None:
            return None

        try:
            soil_type = self.soil_classifier.predict(image_path)
            self.data["soil_type"] = soil_type
            return soil_type
        except Exception as e:
            print("Error en clasificador de suelo:", e)
            return None

    def get_state(self):
        """
        Devuelve el estado actual de sensores.
        Si falta un valor, se usa fallback o valores random.
        """
        now = int(time.time() * 1000)
        return {
            "soil_moisture": self.data.get("soil_moisture", "not found"),
            "temperature": self.data.get("temperature", round(random.uniform(16.0, 17.0), 1)),
            "air_humidity": self.data.get("air_humidity", random.randint(80, 85)),
            "soil_type": self.data.get("soil_type", "not found"),
            "ts": str(now),
        }

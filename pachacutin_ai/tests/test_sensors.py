import time
import requests

URL = "http://127.0.0.1:5000/sensors"  # 👈 usa tu Flask local
# Si estás probando con Ngrok desde el celular:
# URL = "https://TU_URL_NGROK.ngrok-free.app/sensors"

def test_sensors():
    """Consulta varias veces el endpoint /sensors y muestra los resultados."""
    for i in range(5):  # 5 lecturas
        try:
            r = requests.get(URL, timeout=5)
            data = r.json()
            print(f"Lectura {i+1}: {data}")
        except Exception as e:
            print(f"⚠️ Error en lectura {i+1}: {e}")
        time.sleep(5)  # esperar 5s entre lecturas

if __name__ == "__main__":
    test_sensors()

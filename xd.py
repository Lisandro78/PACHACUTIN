# bootstrap_pachacutin_unified.py
# Crea la estructura pachacutin_unified/ con TODO el código dentro.
# Uso:
#   python3 bootstrap_pachacutin_unified.py            # en el directorio actual
#   python3 bootstrap_pachacutin_unified.py /ruta/destino

import sys, os
from pathlib import Path

BASE_DIR = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
PKG_DIR  = BASE_DIR / "pachacutin_unified"

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"[OK] {path.relative_to(BASE_DIR)}")

print(f">> Creando estructura en: {PKG_DIR}")

# -------------------- archivos --------------------
files = {
    # paquete raíz
    PKG_DIR / "__init__.py": """# Marca de paquete\n""",

    PKG_DIR / "run_unified.py": r'''# -*- coding: utf-8 -*-
import logging
from flask import Flask
from flask_cors import CORS

from pachacutin_unified.config import HOST, PORT, DEBUG
from pachacutin_unified.blueprints.unified import unified_bp

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.after_request
    def _no_cache(resp):
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp

    app.register_blueprint(unified_bp)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host=HOST, port=PORT, debug=DEBUG)
''',

    PKG_DIR / "config.py": r'''# -*- coding: utf-8 -*-
import os

# Servidor
HOST  = os.environ.get("PACHACUTIN_HOST", "0.0.0.0")
PORT  = int(os.environ.get("PACHACUTIN_PORT", "5000"))
DEBUG = os.environ.get("PACHACUTIN_DEBUG", "1") == "1"

# Seguridad simple
TOKEN = os.environ.get("PACHACUTIN_TOKEN", "pachacutin2025")

# Rutas de archivos
BASE_DIR    = os.path.dirname(__file__)
STATIC_DIR  = os.path.join(BASE_DIR, "static")
CAPTURE_DIR = os.path.join(STATIC_DIR, "captures")
os.makedirs(CAPTURE_DIR, exist_ok=True)

# Cámara
CAM_INDEX = os.environ.get("PACHACUTIN_CAM_INDEX")  # "0","1","2"... o None
CAM_TRY_INDICES = [0,1,2,3]

# Serial (Arduino)
SERIAL_PORT = os.environ.get("PACHACUTIN_SERIAL", "").strip()   # p.ej. /dev/ttyACM0
SERIAL_BAUD = int(os.environ.get("PACHACUTIN_BAUD", "115200"))

# OpenAI (opcional)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL   = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
''',

    # blueprints
    PKG_DIR / "blueprints" / "__init__.py": """# paquete de blueprints\n""",

    PKG_DIR / "blueprints" / "video.py": r'''# -*- coding: utf-8 -*-
import time, logging
from typing import Optional
try:
    import cv2
except Exception as e:
    cv2 = None
    logging.warning("OpenCV no disponible: %s", e)

from pachacutin_unified.config import CAM_INDEX, CAM_TRY_INDICES

class VideoStreamer:
    def __init__(self):
        self.cap = None
        self.enabled = False

    def _open_any(self) -> Optional["cv2.VideoCapture"]:
        if cv2 is None:
            return None
        indices = []
        if CAM_INDEX is not None:
            try:
                indices.append(int(CAM_INDEX))
            except:
                pass
        indices += CAM_TRY_INDICES
        seen = set()
        for i in indices:
            if i in seen:
                continue
            seen.add(i)
            cap = cv2.VideoCapture(i)
            if cap is not None and cap.isOpened():
                logging.info("Cámara abierta en /dev/video%d", i)
                return cap
            if cap is not None:
                cap.release()
        logging.error("No se pudo abrir ninguna cámara.")
        return None

    def start(self):
        self.enabled = True

    def stop(self):
        self.enabled = False
        if self.cap is not None:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None

    def get_frame(self):
        if cv2 is None or not self.enabled:
            return None
        if self.cap is None or not self.cap.isOpened():
            self.cap = self._open_any()
            if self.cap is None:
                return None
        ok, frame = self.cap.read()
        if not ok:
            time.sleep(0.02)
            return None
        return frame

    def mjpeg_generator(self):
        if cv2 is None:
            while self.enabled:
                yield (b"--frame\r\nContent-Type: text/plain\r\n\r\nOpenCV no disponible\r\n\r\n")
                time.sleep(1.0)
            return
        while self.enabled:
            frame = self.get_frame()
            if frame is None:
                time.sleep(0.2)
                continue
            ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ok:
                continue
            jpg = buffer.tobytes()
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n")

streamer = VideoStreamer()
''',

    # services
    PKG_DIR / "services" / "__init__.py": """# paquete de servicios\n""",

    PKG_DIR / "services" / "serial_bridge.py": r'''# -*- coding: utf-8 -*-
import logging
from pachacutin_unified.config import SERIAL_PORT, SERIAL_BAUD

class SerialBridge:
    def __init__(self):
        self.ser = None
        if SERIAL_PORT:
            try:
                import serial
                self.ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.2)
                logging.info("Serial abierto en %s @ %d", SERIAL_PORT, SERIAL_BAUD)
            except Exception as e:
                logging.error("No se pudo abrir serial %s: %s", SERIAL_PORT, e)

    def send(self, line: str) -> bool:
        if self.ser is None:
            logging.info("Serial no disponible; comando '%s' ignorado.", line)
            return False
        try:
            if not line.endswith("\n"):
                line += "\n"
            self.ser.write(line.encode("utf-8"))
            return True
        except Exception as e:
            logging.error("Error enviando por serial: %s", e)
            return False

serial_bridge = SerialBridge()
''',

    PKG_DIR / "services" / "sensor_manager.py": r'''# -*- coding: utf-8 -*-
import random, time, threading
import logging
from typing import Optional

from pachacutin_unified.config import SERIAL_PORT, SERIAL_BAUD
try:
    import serial
except Exception:
    serial = None

class SensorManager:
    """
    - soil_moisture: desde Arduino por serial (si hay), si no, emula.
    - temperature, air_humidity: aleatorios (suaves).
    - soil_type: lo setea el clasificador o queda previo.
    - Solo corre cuando enabled=True (activado por /mode).
    """
    def __init__(self):
        self.enabled = False
        self.thread = None
        self.stop_evt = threading.Event()

        self.soil_moisture: int = 40
        self.temperature: float = 22.5
        self.air_humidity: int = 55
        self.soil_type: str = "Desconocido"

        self._ser = None

    def _open_serial(self):
        if SERIAL_PORT and serial is not None:
            try:
                self._ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.2)
                logging.info("Sensor serial abierto en %s", SERIAL_PORT)
            except Exception as e:
                logging.error("No se pudo abrir serial para sensores: %s", e)
                self._ser = None

    def _tick_randoms(self):
        self.temperature += random.uniform(-0.2, 0.2)
        self.temperature = max(10.0, min(40.0, self.temperature))
        self.air_humidity += random.randint(-1, 1)
        self.air_humidity = max(10, min(90, self.air_humidity))

    def _read_serial_line(self) -> Optional[str]:
        if self._ser is None:
            return None
        try:
            if self._ser.in_waiting:
                line = self._ser.readline().decode("utf-8", errors="ignore").strip()
                return line
        except Exception:
            return None
        return None

    def _parse_line(self, line: str):
        """
        Acepta formatos:
          MOIST=41
          TMP=22.3;HUMS=41;HUMA=58;SOIL=Arenoso
        Sólo nos comprometemos a leer MOIST (humedad suelo).
        """
        if "MOIST=" in line:
            try:
                v = int(line.split("MOIST=",1)[1].split(";")[0])
                self.soil_moisture = max(0, min(100, v))
            except:
                pass

    def _loop(self):
        self._open_serial()
        while not self.stop_evt.is_set():
            if not self.enabled:
                time.sleep(0.1)
                continue

            line = self._read_serial_line()
            if line:
                self._parse_line(line)
            else:
                if self._ser is None:
                    self.soil_moisture += random.randint(-1, 1)
                    self.soil_moisture = max(0, min(100, self.soil_moisture))

            self._tick_randoms()
            time.sleep(0.5)

        if self._ser is not None:
            try:
                self._ser.close()
            except:
                pass
            self._ser = None

    def start(self):
        if self.thread and self.thread.is_alive():
            self.enabled = True
            return
        self.stop_evt.clear()
        self.enabled = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.enabled = False  # pausa

    def get_payload(self):
        return {
            "soil_type": self.soil_type,
            "temperature": round(self.temperature, 1),
            "soil_moisture": int(self.soil_moisture),
            "air_humidity": int(self.air_humidity),
        }

    def set_soil_type(self, s: str):
        self.soil_type = s or "Desconocido"

sensors = SensorManager()
''',

    PKG_DIR / "services" / "soil_classifier.py": r'''# -*- coding: utf-8 -*-
"""
Clasificador de tipo de suelo (placeholder).
Conecta aquí tu modelo real luego. Por ahora usa brillo promedio.
"""
def classify_soil_from_bgr_image(img_bgr) -> str:
    if img_bgr is None:
        return "Desconocido"
    import cv2
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    mean = float(gray.mean())
    if mean < 60:
        return "Arcilloso"
    elif mean < 120:
        return "Franco"
    elif mean < 180:
        return "Arenoso"
    else:
        return "Gravoso"
''',

    PKG_DIR / "services" / "recommender.py": r'''# -*- coding: utf-8 -*-
from pachacutin_unified.config import OPENAI_API_KEY, OPENAI_MODEL

def rule_based_rec(payload: dict) -> str:
    soil = (payload.get("soil_type") or "").lower()
    hum  = int(payload.get("soil_moisture") or 0)
    temp = float(payload.get("temperature") or 0)
    if "aren" in soil and 25 <= temp <= 35 and hum >= 30:
        return "Siembra algarrobo; suelo arenoso con buena temperatura y humedad."
    if hum < 20:
        return "Riega primero; la humedad del suelo es muy baja para sembrar."
    if "arcill" in soil:
        return "Siembra molle costeño; tolera suelos arcillosos."
    return "Siembra huarango o faique; condiciones generales aceptables."

def openai_rec(payload: dict) -> str:
    if not OPENAI_API_KEY:
        return rule_based_rec(payload)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        content = (
            "Eres un asistente agrícola. Con los siguientes datos sugiere UNA sola semilla a sembrar "
            "en costa árida del Perú (Callao), y una breve razón (≤15 palabras). "
            f"Datos: soil_type={payload.get('soil_type')}, soil_moisture={payload.get('soil_moisture')}%, "
            f"air_humidity={payload.get('air_humidity')}%, temperature={payload.get('temperature')}°C."
        )
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role":"system","content":"Eres un agrónomo experto."},
                      {"role":"user","content":content}],
            temperature=0.2,
            max_tokens=70,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return rule_based_rec(payload)

def get_recommendation(payload: dict) -> str:
    return openai_rec(payload)
''',

    # unified blueprint (endpoints para tus bloques)
    PKG_DIR / "blueprints" / "unified.py": r'''# -*- coding: utf-8 -*-
import os, time, logging
from flask import Blueprint, jsonify, request, Response, send_from_directory

from pachacutin_unified.config import TOKEN, CAPTURE_DIR
from pachacutin_unified.blueprints.video import streamer
from pachacutin_unified.services.sensor_manager import sensors
from pachacutin_unified.services.serial_bridge import serial_bridge
from pachacutin_unified.services.soil_classifier import classify_soil_from_bgr_image
from pachacutin_unified.services.recommender import get_recommendation

unified_bp = Blueprint("unified", __name__)

# -------------------- MODO / ACTIVACIÓN POR PANTALLA --------------------
@unified_bp.route("/mode")
def mode():
    m = (request.args.get("m") or "").lower()
    _ = request.args.get("token", "")  # token opcional
    if m not in {"monitor","sensors","control","idle"}:
        return jsonify({"ok": False, "error": "bad mode"}), 400

    # Apaga todo primero
    streamer.stop()
    sensors.stop()
    state = {"monitor": False, "sensors": False, "control": False}

    if m == "monitor":
        streamer.start()
        state["monitor"] = True
    elif m == "sensors":
        sensors.start()
        state["sensors"] = True
    elif m == "control":
        state["control"] = True
    elif m == "idle":
        pass

    return jsonify({"ok": True, "mode": m, "state": state}), 200

# -------------------- STREAM --------------------
@unified_bp.route("/live")
def live():
    if not streamer.enabled:
        return Response(b"Monitor desactivado (entra a Monitoreo Visual).",
                        status=409, mimetype="text/plain")
    return Response(streamer.mjpeg_generator(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@unified_bp.route("/video_feed")
def video_feed():
    return live()

# -------------------- SENSORES --------------------
@unified_bp.route("/sensors")
def sensors_endpoint():
    if not sensors.enabled:
        return jsonify({"soil_type": sensors.soil_type,
                        "temperature": None,
                        "soil_moisture": None,
                        "air_humidity": None,
                        "error": "sensors_disabled"}), 409
    return jsonify(sensors.get_payload()), 200

# -------------------- CAPTURA --------------------
@unified_bp.route("/capture")
def capture():
    if not streamer.enabled:
        return jsonify({"ok": False, "error": "monitor_disabled"}), 409

    frame = streamer.get_frame()
    if frame is None:
        return jsonify({"ok": False, "error": "no_frame"}), 500

    ts_ms = int(time.time() * 1000)
    filename = f"capture_{ts_ms}.jpg"
    path = os.path.join(CAPTURE_DIR, filename)
    try:
        import cv2
        ok = cv2.imwrite(path, frame)
        if not ok:
            raise RuntimeError("cv2.imwrite False")
    except Exception:
        open(path, "ab").close()

    base = request.host_url.rstrip("/")
    full_url = f"{base}/captures/{filename}"
    return jsonify({"ok": True,
                    "filename": filename,
                    "full_url_nocache": f"{full_url}?ts={ts_ms}"}), 200

@unified_bp.route("/captures/<path:name>")
def serve_captures(name):
    return send_from_directory(CAPTURE_DIR, name)

# -------------------- CLASIFICADOR DE SUELO --------------------
@unified_bp.route("/classify_soil")
def classify_soil():
    frame = streamer.get_frame()
    if frame is None:
        return jsonify({"ok": False, "error": "no_frame"}), 500
    soil = classify_soil_from_bgr_image(frame)
    sensors.set_soil_type(soil)
    return jsonify({"ok": True, "soil_type": soil}), 200

@unified_bp.route("/set_soil_type")
def set_soil_type():
    soil = request.args.get("soil_type", "").strip() or "Desconocido"
    sensors.set_soil_type(soil)
    return jsonify({"ok": True, "soil_type": soil}), 200

# -------------------- RECOMENDACIÓN --------------------
@unified_bp.route("/recommendation")
def recommendation():
    payload = sensors.get_payload()
    rec = get_recommendation(payload)
    return jsonify({"recommendation": rec}), 200

# -------------------- CONTROL MANUAL --------------------
@unified_bp.route("/cmd")
def cmd():
    token = request.args.get("token", "")
    if token != TOKEN:
        return jsonify({"ok": False, "error": "bad token"}), 401

    c = (request.args.get("c") or "").upper()
    mapping = {
        "A": "perforar_down",
        "W": "stop",
        "B": "retirar_broca",
        "C": "giro_antihorario",
        "D": "giro_horario",
        "U": "stop_giro",
    }
    action = mapping.get(c)
    if not action:
        return jsonify({"ok": False, "error": "bad cmd"}), 400

    logging.info("CMD %s -> %s", c, action)
    serial_bridge.send(action)
    return jsonify({"ok": True, "action": action}), 200
'''
}

# -------------------- escribir archivos --------------------
for p, c in files.items():
    write(p, c)

# crear carpeta de capturas
(PKG_DIR / "static" / "captures").mkdir(parents=True, exist_ok=True)
print("[OK] pachacutin_unified/static/captures/ (directorio)")

print("\n--- Hecho ---")
print("Instala deps y ejecuta:")
print("  sudo apt update && sudo apt install -y python3-venv python3-opencv v4l-utils")
print("  python3 -m venv .venv && source .venv/bin/activate")
print("  pip install -U pip flask flask-cors pyserial")
print("  python3 pachacutin_unified/run_unified.py")
print("\nEndpoints:")
print("  /mode?m=sensors | monitor | control | idle")
print("  /sensors   /live   /capture   /recommendation   /cmd?c=A&token=pachacutin2025")

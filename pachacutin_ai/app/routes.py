
# pachacutin_ai/app/routes.py

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from flask import Blueprint, jsonify, request
from pachacutin_ai.app import background_tasks as bt
from pachacutin_ai.app.recommender import get_recommendation

# CORS opcional
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except Exception:
    CORS_AVAILABLE = False

bp = Blueprint("routes", __name__)
if CORS_AVAILABLE:
    CORS(bp, resources={r"/*": {"origins": "*"}})

# --- Ejecutores / timeouts ---
_EXECUTOR = ThreadPoolExecutor(max_workers=2)
_DEFAULT_RECO_TIMEOUT_MS = 25000  # 25 s

# --- Semillas permitidas (nativas/adaptadas a costa limeña) ---
ALLOWED_SEEDS = [
    {"id": "pallar",       "common": "Pallar (lima bean)", "latin": "Phaseolus lunatus"},
    {"id": "aji_amarillo", "common": "Ají amarillo",       "latin": "Capsicum baccatum"},
    {"id": "camote",       "common": "Camote",             "latin": "Ipomoea batatas"},
    {"id": "algarrobo",    "common": "Algarrobo (huarango)","latin": "Prosopis pallida"},
]

@bp.after_request
def add_headers(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

def _snapshot():
    """Toma una instantánea de sensores + lista de semillas permitidas."""
    soil_type = "Desconocido"
    soil_moisture = 40.0
    air_humidity = 90.0
    temperature = 16.0

    lock = getattr(bt, "lock", None)
    if lock:
        try:
            with lock:
                soil_type = getattr(bt, "latest_soil_type", soil_type) or soil_type
                latest_soil = getattr(bt, "latest_soil", {}) or {}
                latest_weather = getattr(bt, "latest_weather", {}) or {}
                soil_moisture = float(latest_soil.get("soil_moisture", soil_moisture))
                temperature   = float(latest_weather.get("temperatura",   temperature))
                air_humidity  = float(latest_weather.get("humedad_aire",  air_humidity))
        except Exception:
            pass
    else:
        try:
            soil_type = getattr(bt, "latest_soil_type", soil_type) or soil_type
            latest_soil = getattr(bt, "latest_soil", {}) or {}
            latest_weather = getattr(bt, "latest_weather", {}) or {}
            soil_moisture = float(latest_soil.get("soil_moisture", soil_moisture))
            temperature   = float(latest_weather.get("temperatura",   temperature))
            air_humidity  = float(latest_weather.get("humedad_aire",  air_humidity))
        except Exception:
            pass

    return {
        "soil_type": soil_type,
        "soil_moisture": soil_moisture,
        "air_humidity": air_humidity,
        "temperature": temperature,
        "allowed_seeds": ALLOWED_SEEDS,  # <-- clave nueva
    }

@bp.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "Pachacutín API activa"})

@bp.route("/sensors", methods=["GET"])
def sensors():
    snap = _snapshot()
    snap["ts"] = time.time()
    return jsonify(snap), 200

@bp.route("/recommendation", methods=["GET"])
def recommendation():
    """
    Calcula la recomendación (solo entre 4 semillas permitidas) con timeout y fallback.
    MIT: WebReco.TiempoEspera=30000 y URL .../recommendation?timeout_ms=25000&ts=...
    """
    try:
        timeout_ms = int(request.args.get("timeout_ms", _DEFAULT_RECO_TIMEOUT_MS))
    except Exception:
        timeout_ms = _DEFAULT_RECO_TIMEOUT_MS
    timeout_ms = max(5000, min(timeout_ms, 55000))
    timeout_s = timeout_ms / 1000.0

    snap = _snapshot()
    t0 = time.time()
    fut = _EXECUTOR.submit(get_recommendation, snap, timeout_s)

    try:
        reco = fut.result(timeout=timeout_s + 1.0)
        took_ms = int((time.time() - t0) * 1000)
        return jsonify({
            "recommendation": reco.get("text", ""),
            "source": reco.get("source", "openai"),
            "took_ms": took_ms,
            "input": snap
        }), 200

    except TimeoutError:
        fut.cancel()
        return jsonify({
            "recommendation": "No pude obtener la recomendación a tiempo. Inténtalo otra vez.",
            "source": "timeout"
        }), 200

    except Exception:
        return jsonify({
            "recommendation": "Ocurrió un error al generar la recomendación.",
            "source": "server_error"
        }), 200

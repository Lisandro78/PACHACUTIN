from flask import Blueprint, jsonify, send_from_directory, url_for, request
import os
import cv2
import time
import config
from blueprints.video import streamer

capture_bp = Blueprint("capture", __name__)

@capture_bp.get("/capture")
def capture_image():
    # asegurar carpeta
    os.makedirs(config.CAPTURE_DIR, exist_ok=True)

    # tomar frame
    frame = streamer.get_frame()
    if frame is None:
        return jsonify({"ok": False, "error": "No hay frame disponible"}), 500

    # guardar archivo
    ts_ms = int(time.time() * 1000)
    filename = f"capture_{ts_ms}.jpg"
    filepath = os.path.join(config.CAPTURE_DIR, filename)
    if not cv2.imwrite(filepath, frame):
        return jsonify({"ok": False, "error": "No se pudo guardar la imagen"}), 500

    # servir SIEMPRE por nuestra propia ruta (/captures/...) —evita problemas con /static
    rel_url = url_for("capture.get_capture", name=filename)                 # /captures/...
    abs_url = url_for("capture.get_capture", name=filename, _external=True) # http://IP:5000/captures/...

    # anti-caché (usa ts de la petición si viene)
    bust = request.args.get("ts") or str(ts_ms)

    return jsonify({
        "ok": True,
        "file": filename,
        "url": rel_url,
        "full_url": abs_url,
        "url_nocache": f"{rel_url}?nocache={bust}",
        "full_url_nocache": f"{abs_url}?nocache={bust}",
        "ts": ts_ms
    })

@capture_bp.get("/captures/<path:name>")
def get_capture(name):
    directory = os.path.abspath(config.CAPTURE_DIR)
    return send_from_directory(directory, name, mimetype="image/jpeg")

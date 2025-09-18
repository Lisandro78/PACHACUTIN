# -*- coding: utf-8 -*-
"""
pachacutin_unified/blueprints/unified.py
Blueprint principal con endpoints:
- /mode          -> activar monitor / sensors / control / idle
- /live, /video_feed
- /sensors
- /capture       -> guarda imagen y ejecuta clasificación (actualiza soil_type)
- /captures/<name>
- /classify_soil
- /set_soil_type
- /recommendation
- /cmd           -> envía letra al Arduino y devuelve lo que respondió
- /debug_cam     -> estado rápido del streamer
"""
import os
import time
import logging
from flask import Blueprint, jsonify, request, Response, send_from_directory

from pachacutin_unified.config import TOKEN, CAPTURE_DIR
from pachacutin_unified.blueprints.video import streamer
from pachacutin_unified.services.sensor_manager import sensors
from pachacutin_unified.services.serial_bridge import serial_bridge
from pachacutin_unified.services.soil_classifier import classify_soil_from_bgr_image
from pachacutin_unified.services.recommender import get_recommendation

logger = logging.getLogger(__name__)
unified_bp = Blueprint("unified", __name__)


# -------------------- MODO / ACTIVACIÓN POR PANTALLA --------------------
@unified_bp.route("/mode")
def mode():
    m = (request.args.get("m") or "").lower()
    _ = request.args.get("token", "")  # token opcional aquí para no romper navegación
    if m not in {"monitor", "sensors", "control", "idle"}:
        return jsonify({"ok": False, "error": "bad mode"}), 400

    # Apagar todo primero
    try:
        streamer.stop()
    except Exception:
        logger.exception("Error al detener streamer")
    try:
        sensors.stop()
    except Exception:
        logger.exception("Error al detener sensores")

    state = {"monitor": False, "sensors": False, "control": False}

    if m == "monitor":
        streamer.start()
        state["monitor"] = True
        logger.info("Mode -> monitor (streamer started)")
    elif m == "sensors":
        sensors.start()
        state["sensors"] = True
        logger.info("Mode -> sensors (sensor manager started)")
    elif m == "control":
        state["control"] = True
        logger.info("Mode -> control")
    elif m == "idle":
        logger.info("Mode -> idle (all stopped)")

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
    try:
        if not sensors.enabled:
            # devolvemos estructura conocida y un error corto para la app
            return jsonify({
                "soil_type": sensors.soil_type,
                "temperature": None,
                "soil_moisture": None,
                "air_humidity": None,
                "error": "sensors_disabled"
            }), 409
        return jsonify(sensors.get_payload()), 200
    except Exception:
        logger.exception("Error en /sensors")
        return jsonify({"error": "server_error"}), 500


# -------------------- CAPTURA (y clasificación automática) --------------------
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
            raise RuntimeError("cv2.imwrite returned False")
    except Exception:
        # crear archivo vacío para no romper rutas
        try:
            open(path, "ab").close()
        except Exception:
            logger.exception("No se pudo escribir archivo de captura")

    # Ejecutar clasificación sobre el frame y actualizar soil_type
    try:
        soil = classify_soil_from_bgr_image(frame)
        sensors.set_soil_type(soil)
        logger.info("Soil classified on capture: %s", soil)
    except Exception:
        logger.exception("Soil classification failed on capture")

    base = request.host_url.rstrip("/")
    full_url = f"{base}/captures/{filename}"
    return jsonify({
        "ok": True,
        "filename": filename,
        "full_url_nocache": f"{full_url}?ts={ts_ms}",
        "soil_type": sensors.soil_type
    }), 200


@unified_bp.route("/captures/<path:name>")
def serve_captures(name):
    return send_from_directory(CAPTURE_DIR, name)


# -------------------- CLASIFICADOR DE SUELO --------------------
@unified_bp.route("/classify_soil")
def classify_soil():
    # Intentar obtener un frame; si no hay, devolver error
    frame = streamer.get_frame()
    if frame is None:
        return jsonify({"ok": False, "error": "no_frame"}), 500
    try:
        soil = classify_soil_from_bgr_image(frame)
        sensors.set_soil_type(soil)
        return jsonify({"ok": True, "soil_type": soil}), 200
    except Exception:
        logger.exception("Error en classify_soil")
        return jsonify({"ok": False, "error": "classification_failed"}), 500


@unified_bp.route("/set_soil_type")
def set_soil_type():
    soil = request.args.get("soil_type", "").strip() or "Desconocido"
    sensors.set_soil_type(soil)
    return jsonify({"ok": True, "soil_type": soil}), 200


# -------------------- RECOMENDACIÓN (OpenAI o regla) --------------------
@unified_bp.route("/recommendation")
def recommendation():
    try:
        payload = sensors.get_payload()
        rec = get_recommendation(payload)
        return jsonify({"recommendation": rec}), 200
    except Exception:
        logger.exception("Error en recommendation")
        return jsonify({"recommendation": "error"}), 500


# -------------------- CONTROL MANUAL (Gateway -> Arduino) --------------------
@unified_bp.route("/cmd")
def cmd():
    token = request.args.get("token", "")
    if token != TOKEN:
        return jsonify({"ok": False, "error": "bad token"}), 401

    c = (request.args.get("c") or "").upper()
    if not c:
        return jsonify({"ok": False, "error": "no command"}), 400

    # mapping para la UI/logs; la letra se envía tal cual al Arduino
    mapping = {
        "A": "perforar_down",
        "W": "stop",
        "B": "retirar_broca",
        "C": "giro_antihorario",
        "D": "giro_horario",
        "U": "stop_giro",
    }
    action_name = mapping.get(c, "raw_letter")

    # enviar la letra y esperar una respuesta corta del Arduino (si la hay)
    try:
        sent, replies = serial_bridge.send_and_get_response(c, wait_ms=500)
    except Exception:
        logger.exception("Error enviando comando serial")
        sent, replies = False, []

    logger.info("CMD request c=%s mapped=%s sent=%s replies=%s", c, action_name, sent, replies)

    return jsonify({
        "ok": True,
        "command": c,
        "mapped": action_name,
        "sent": bool(sent),
        "arduino_reply": replies
    }), 200


# -------------------- DEBUG: estado de cámara / streamer --------------------
@unified_bp.route("/debug_cam")
def debug_cam():
    try:
        cap = getattr(streamer, "cap", None)
        is_open = False
        try:
            is_open = bool(cap is not None and cap.isOpened())
        except Exception:
            is_open = False
        return jsonify({
            "streamer_enabled": bool(streamer.enabled),
            "cap_is_open": is_open,
            "current_soil_type": sensors.soil_type
        }), 200
    except Exception:
        logger.exception("Error en debug_cam")
        return jsonify({"ok": False}), 500

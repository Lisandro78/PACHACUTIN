from flask import Flask
from . import config
from .api import bp as api_bp
import os, sys

def create_app(manager):
    app = Flask(__name__)
    app.config.from_object(config)
    app.module_manager = manager
    app.register_blueprint(api_bp)

    # 🔌 Importar y registrar blueprints de usb_cam_server si existen
    try:
        # server.py está en pachacutin_unified/pachacutin_unified/
        # subimos 3 niveles para llegar a la raíz del repo (pachacutin_ai)
        cam_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "usb_cam_server")
        )
        sys.path.insert(0, cam_path)
        # Ajusta estos imports si tus nombres difieren:
        from blueprints.video import video_bp
        from blueprints.capture import capture_bp
        app.register_blueprint(video_bp)      # mantiene /video/*
        app.register_blueprint(capture_bp)    # mantiene /capture
        print("usb_cam_server blueprints registrados (/video, /capture).")
    except Exception as e:
        print("usb_cam_server no integrado (blueprints no encontrados):", e)

    return app

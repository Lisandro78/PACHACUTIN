# pachacutin_unified/pachacutin_unified/server.py
from flask import Flask, Response, stream_with_context, request
from . import config
from .api import bp as api_bp
import os, sys, importlib, traceback

def _register_usb_cam_blueprints(app: Flask):
    """
    Intenta integrar 'usb_cam_server' de tres formas:
      1) Carga explícita de blueprints: blueprints.video / blueprints.capture
      2) Auto-descubrimiento: registra cualquier flask.Blueprint encontrado
      3) Fallback proxy: si UNIFIED_USB_CAM_URL está definido, crea /live y /capture como proxy
    """
    cam_path = config.USB_CAM_SERVER_PATH  # por defecto ../usb_cam_server
    cam_url  = os.environ.get("UNIFIED_USB_CAM_URL")  # opcional, ej: http://127.0.0.1:8080
    found = False

    # 1) Import directo de blueprints esperados
    try:
        if cam_path:
            sys.path.insert(0, os.path.abspath(cam_path))
        from blueprints.video import video_bp  # type: ignore
        app.register_blueprint(video_bp)
        print("usb_cam_server: 'video_bp' registrado.")
        found = True
    except Exception as e:
        print("usb_cam_server: no se pudo registrar 'video_bp':", e)

    try:
        from blueprints.capture import capture_bp  # type: ignore
        app.register_blueprint(capture_bp)
        print("usb_cam_server: 'capture_bp' registrado.")
        found = True
    except Exception as e:
        print("usb_cam_server: no se pudo registrar 'capture_bp':", e)

    # 2) Auto-descubrimiento de cualquier Blueprint
    if not found and cam_path and os.path.isdir(os.path.abspath(cam_path)):
        try:
            from flask import Blueprint  # para isinstance
            base = os.path.abspath(cam_path)
            if base not in sys.path:
                sys.path.insert(0, base)

            for root, _, files in os.walk(base):
                for fname in files:
                    if not fname.endswith(".py"):
                        continue
                    modname = os.path.splitext(os.path.relpath(os.path.join(root, fname), base))[0]
                    modname = modname.replace(os.sep, ".")
                    try:
                        m = importlib.import_module(modname)
                        for attr in dir(m):
                            obj = getattr(m, attr, None)
                            if obj is not None and isinstance(obj, Blueprint):
                                app.register_blueprint(obj)
                                print(f"usb_cam_server: Blueprint registrado desde {modname}.{attr}")
                                found = True
                    except Exception:
                        # no rompemos por módulos que no carguen
                        pass
        except Exception as e:
            print("usb_cam_server: error en auto-descubrimiento:", e)

    # 3) Fallback: proxy si hay URL externa definida
    if not found and cam_url:
        print("usb_cam_server: blueprints no encontrados; habilitando proxy a", cam_url)
        import requests

        @app.route("/live")
        def _cam_live_proxy():
            url = cam_url.rstrip("/") + "/live"
            upstream = requests.get(url, stream=True, timeout=10)
            # reenviamos el stream (mjpeg u otro)
            return Response(
                stream_with_context(upstream.iter_content(8192)),
                status=upstream.status_code,
                headers={
                    "Content-Type": upstream.headers.get("Content-Type", "application/octet-stream")
                },
            )

        @app.route("/capture", methods=["GET", "POST"])
        def _cam_capture_proxy():
            url = cam_url.rstrip("/") + "/capture"
            if request.method == "POST":
                upstream = requests.post(
                    url,
                    data=request.get_data(),
                    headers={"Content-Type": request.headers.get("Content-Type", "application/json")},
                    timeout=15,
                )
            else:
                upstream = requests.get(url, timeout=15)
            return (upstream.content, upstream.status_code, {
                "Content-Type": upstream.headers.get("Content-Type", "application/json")
            })
        found = True

    if not found:
        print("usb_cam_server no integrado (no se encontraron blueprints y no hay UNIFIED_USB_CAM_URL).")
    else:
        print("usb_cam_server integrado.")

def create_app(manager):
    app = Flask(__name__)
    app.config.from_object(config)
    app.module_manager = manager
    app.register_blueprint(api_bp)

    # integrar cámara (si existe)
    try:
        _register_usb_cam_blueprints(app)
    except Exception as e:
        print("usb_cam_server: excepción durante el registro:", e)
        traceback.print_exc()

    return app

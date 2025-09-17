import os
from flask import Flask
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except Exception:
    CORS_AVAILABLE = False


def create_app():
    # fija la carpeta /static explícitamente (evita 404)
    here = os.path.dirname(os.path.abspath(__file__))
    app = Flask(
        __name__,
        static_folder=os.path.join(here, "static"),
        static_url_path="/static",
    )

    if CORS_AVAILABLE:
        CORS(app)

    # importa y registra blueprints después de crear app
    from blueprints.video import video_bp
    from blueprints.capture import capture_bp
    app.register_blueprint(video_bp)
    app.register_blueprint(capture_bp)
    return app

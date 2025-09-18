# -*- coding: utf-8 -*-
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

from flask import Flask

def create_app():
    app = Flask(__name__)
    # configura si hace falta (se puede usar app.config.from_object)
    from . import config
    app.config.from_object(config)
    # registra blueprint
    from .api import bp as api_bp
    app.register_blueprint(api_bp)
    return app

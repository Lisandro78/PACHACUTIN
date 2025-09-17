# pachacutin_ai/run.py

from flask import Flask
from pachacutin_ai.app.routes import bp
from pachacutin_ai.app.background_tasks import start_background_tasks

def create_app():
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app

if __name__ == "__main__":
    # Iniciar hilos UNA sola vez (lectura de Arduino, clima, cámara, etc.)
    start_background_tasks()

    app = create_app()
    # Servir por red local, sin reloader, con threads
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True, use_reloader=False)

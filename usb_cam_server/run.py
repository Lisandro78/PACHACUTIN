from app import create_app
import config
import os

os.makedirs(config.CAPTURE_DIR, exist_ok=True)
app = create_app()

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, threaded=True)

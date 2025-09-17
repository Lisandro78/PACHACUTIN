from flask import Blueprint, Response, render_template
import time
import config
from camera.streamer import CameraStreamer

video_bp = Blueprint("video", __name__)

# Inicializar la cámara USB
streamer = CameraStreamer(
    index=config.CAMERA_INDEX,
    width=config.WIDTH,
    height=config.HEIGHT,
    fps=config.FPS,
    jpeg_quality=config.JPEG_QUALITY
)
streamer.start()

def mjpeg_generator():
    boundary = b"--frame"
    while True:
        jpeg = streamer.get_jpeg()
        if jpeg is None:
            time.sleep(0.1)
            continue
        yield (
            boundary + b"\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
        )
        time.sleep(0.05)  # controla el envío (~20 fps máx)

@video_bp.get("/video")
def video_stream():
    return Response(mjpeg_generator(), mimetype="multipart/x-mixed-replace; boundary=frame")

@video_bp.get("/live")
def live_page():
    return render_template("live.html")

import cv2
import time
import threading
import config

class CameraStreamer:
    def __init__(self, index=0, width=640, height=480, fps=15, jpeg_quality=70):
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self.jpeg_quality = jpeg_quality
        self._cap = None
        self._running = False
        self._thread = None
        self._frame_lock = threading.Lock()
        self._last_frame = None

    def start(self):
        if self._running:
            return
        print(f"[INFO] Usando índice de cámara: {self.index}")
        self._cap = cv2.VideoCapture(self.index)

        # 👉 Forzar MJPEG nativo de la cámara (reduce lag si la soporta)
        self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap.set(cv2.CAP_PROP_FPS, self.fps)

        if not self._cap.isOpened():
            raise RuntimeError("❌ No se pudo abrir la cámara")

        self._running = True
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        if self._cap:
            self._cap.release()
        self._thread = None
        self._cap = None

    def _reader_loop(self):
        delay = 1.0 / max(self.fps, 1)
        while self._running and self._cap:
            ok, frame = self._cap.read()
            if not ok:
                time.sleep(0.05)
                continue
            with self._frame_lock:
                self._last_frame = cv2.resize(frame, (self.width, self.height))
            time.sleep(delay)

    def get_frame(self):
        with self._frame_lock:
            return self._last_frame

    def get_jpeg(self):
        frame = self.get_frame()
        if frame is None:
            return None
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality])
        if not ok:
            return None
        return buf.tobytes()

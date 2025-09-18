# -*- coding: utf-8 -*-
import time, logging
from typing import Optional
try:
    import cv2
except Exception as e:
    cv2 = None
    logging.warning("OpenCV no disponible: %s", e)

from pachacutin_unified.config import CAM_INDEX, CAM_TRY_INDICES

class VideoStreamer:
    def __init__(self):
        self.cap = None
        self.enabled = False

    def _open_any(self) -> Optional["cv2.VideoCapture"]:
        if cv2 is None:
            return None
        indices = []
        if CAM_INDEX is not None:
            try:
                indices.append(int(CAM_INDEX))
            except:
                pass
        indices += CAM_TRY_INDICES
        seen = set()
        for i in indices:
            if i in seen:
                continue
            seen.add(i)
            cap = cv2.VideoCapture(i)
            if cap is not None and cap.isOpened():
                logging.info("Cámara abierta en /dev/video%d", i)
                return cap
            if cap is not None:
                cap.release()
        logging.error("No se pudo abrir ninguna cámara.")
        return None

    def start(self):
        self.enabled = True

    def stop(self):
        self.enabled = False
        if self.cap is not None:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None

    def get_frame(self):
        if cv2 is None or not self.enabled:
            return None
        if self.cap is None or not self.cap.isOpened():
            self.cap = self._open_any()
            if self.cap is None:
                return None
        ok, frame = self.cap.read()
        if not ok:
            time.sleep(0.02)
            return None
        return frame

    def mjpeg_generator(self):
        if cv2 is None:
            while self.enabled:
                yield (b"--frame\r\nContent-Type: text/plain\r\n\r\nOpenCV no disponible\r\n\r\n")
                time.sleep(1.0)
            return
        while self.enabled:
            frame = self.get_frame()
            if frame is None:
                time.sleep(0.2)
                continue
            ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ok:
                continue
            jpg = buffer.tobytes()
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n")

streamer = VideoStreamer()

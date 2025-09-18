# pachacutin_unified/services/serial_bridge.py
# Robust Serial bridge: reintento de apertura, envío con lectura de respuesta,
# y logging para ver en la terminal de Python lo que ocurre.
import logging
import time
from pachacutin_unified.config import SERIAL_PORT, SERIAL_BAUD

_log = logging.getLogger(__name__)

class SerialBridge:
    def __init__(self):
        self.ser = None
        self._last_open_attempt = 0.0
        self._open_interval = 2.0  # segundos entre reintentos de abrir
        # intentar abrir al inicio si hay SERIAL_PORT
        if SERIAL_PORT:
            self._try_open(initial=True)

    def _try_open(self, initial=False):
        """Intenta abrir el puerto serial. Retorna True si lo abrió."""
        if not SERIAL_PORT:
            _log.debug("SerialBridge: SERIAL_PORT no configurado.")
            return False
        now = time.time()
        if not initial and (now - self._last_open_attempt) < self._open_interval:
            return False
        self._last_open_attempt = now
        try:
            import serial
            baud = int(SERIAL_BAUD) if SERIAL_BAUD else 115200
            self.ser = serial.Serial(SERIAL_PORT, baud, timeout=0.2)
            _log.info("SerialBridge: puerto abierto en %s @ %s", SERIAL_PORT, baud)
            # limpiar buffer de lectura inicial
            try:
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
            except Exception:
                pass
            return True
        except Exception as e:
            self.ser = None
            _log.warning("SerialBridge: no se pudo abrir %s -> %s", SERIAL_PORT, e)
            return False

    def _ensure_open(self):
        if self.ser is not None:
            try:
                if self.ser.is_open:
                    return True
            except Exception:
                self.ser = None
        return self._try_open()

    def send_and_get_response(self, text: str, wait_ms: int = 400):
        """
        Envía `text` (string) añadiendo newline si falta.
        Espera hasta `wait_ms` ms leyendo líneas que Arduino devuelva y las retorna.
        Retorna (sent_bool, [lineas_recibidas]).
        """
        if not SERIAL_PORT:
            _log.warning("SerialBridge: SERIAL_PORT no configurado. Mensaje descartado: %s", repr(text))
            return False, []

        if not self._ensure_open():
            _log.warning("SerialBridge: puerto no abierto; no se puede enviar: %s", repr(text))
            return False, []

        try:
            out = text
            if not out.endswith("\n"):
                out = out + "\n"
            self.ser.write(out.encode("utf-8"))
            self.ser.flush()
            _log.info("SerialBridge: enviado -> %s", repr(text))
        except Exception as e:
            _log.error("SerialBridge: error enviando por serial: %s", e)
            try:
                self.ser.close()
            except:
                pass
            self.ser = None
            return False, []

        # ahora leer respuestas que Arduino pueda haber impreso en un pequeño intervalo
        buf_lines = []
        deadline = time.time() + (wait_ms / 1000.0)
        try:
            # leer mientras haya datos o hasta timeout
            while time.time() < deadline:
                try:
                    if self.ser.in_waiting:
                        raw = self.ser.readline()
                        if not raw:
                            continue
                        try:
                            line = raw.decode("utf-8", errors="replace").strip()
                        except Exception:
                            line = repr(raw)
                        if line != "":
                            buf_lines.append(line)
                            _log.info("SerialBridge: recibido -> %s", line)
                        # continue reading until timeout to gather multiple lines
                    else:
                        # si no hay datos, espera un poco antes de volver a preguntar
                        time.sleep(0.01)
                except Exception as e:
                    _log.debug("SerialBridge: error leyendo serial: %s", e)
                    break
        except Exception as e:
            _log.debug("SerialBridge: excepción durante lectura: %s", e)

        return True, buf_lines

    # retrocompatibilidad: send(text) -> solo envía y no espera respuesta
    def send(self, text: str):
        sent, lines = self.send_and_get_response(text, wait_ms=200)
        return sent

# instancia global usada por blueprints
serial_bridge = SerialBridge()

# -*- coding: utf-8 -*-
"""
SensorManager actualizado para leer las líneas JSON que envía tu Arduino:
Ejemplos de línea esperada:
  {"soil_moisture":69}
  {"soil_moisture":56}

- soil_moisture: se obtiene SOLO desde serial (JSON). Si aún no llega lectura válida, será None.
- temperature: aleatorio suave 15.0..18.0 °C
- air_humidity: aleatorio suave 80..85 %
- start() activa el hilo; stop() lo pausa.
"""

import json
import time
import random
import threading
import logging
from typing import Optional

from pachacutin_unified.config import SERIAL_PORT, SERIAL_BAUD

try:
    import serial
except Exception:
    serial = None

_log = logging.getLogger(__name__)

class SensorManager:
    def __init__(self):
        self.enabled = False
        self.thread: Optional[threading.Thread] = None
        self.stop_evt = threading.Event()

        # soil_moisture solo desde Arduino JSON
        self.soil_moisture: Optional[int] = None

        # Añadido: tipo de suelo (por defecto)
        self.soil_type: str = "Desconocido"

        # env randoms (rango pedido)
        self.temperature: float = 16.5  # midpoint 15..18
        self.air_humidity: int = 82     # midpoint 80..85

        self.last_soil_ts: Optional[float] = None

        self._ser = None

    def _open_serial(self):
        if not SERIAL_PORT:
            _log.warning("No hay SERIAL_PORT configurado (PACHACUTIN_SERIAL).")
            return
        if serial is None:
            _log.error("pyserial no disponible; instala pyserial (pip install pyserial).")
            return
        try:
            self._ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.5)
            _log.info("Sensor serial abierto en %s @ %d", SERIAL_PORT, SERIAL_BAUD)
        except Exception as e:
            _log.error("Fallo abriendo serial %s: %s", SERIAL_PORT, e)
            self._ser = None

    def _close_serial(self):
        try:
            if self._ser is not None:
                self._ser.close()
        except Exception:
            pass
        self._ser = None

    def _parse_moist_from_line(self, line: str) -> Optional[int]:
        """
        Espera una línea JSON con clave 'soil_moisture'.
        Ej: {"soil_moisture":69}
        Si no es JSON válido o no contiene la clave, retorna None.
        """
        if not line:
            return None
        line = line.strip()
        try:
            # Si la línea comienza con '{' intentamos parsear JSON
            if line.startswith("{"):
                obj = json.loads(line)
                if isinstance(obj, dict) and "soil_moisture" in obj:
                    v = obj["soil_moisture"]
                    # aceptar números o strings numéricos
                    try:
                        v = int(v)
                    except:
                        return None
                    return max(0, min(100, v))
        except Exception as e:
            _log.debug("JSON parse error: %s | line: %s", e, line)
            return None
        # no JSON válido con soil_moisture
        return None

    def _read_serial_line(self) -> Optional[str]:
        """Lee una línea desde serial si está abierta (retorna str o None)."""
        if self._ser is None:
            return None
        try:
            if self._ser.in_waiting:
                raw = self._ser.readline()
                if not raw:
                    return None
                try:
                    return raw.decode("utf-8", errors="ignore").strip()
                except:
                    return None
        except Exception as e:
            _log.debug("Error leyendo serial: %s", e)
            try:
                self._ser.close()
            except:
                pass
            self._ser = None
            return None
        return None

    def _tick_env_randoms(self):
        """Mantiene temperature entre 15.0..18.0 y air_humidity entre 80..85."""
        self.temperature += random.uniform(-0.15, 0.15)
        self.temperature = max(15.0, min(18.0, self.temperature))
        self.air_humidity += random.randint(-1, 1)
        self.air_humidity = max(80, min(85, self.air_humidity))

    def _loop(self):
        self._open_serial()
        while not self.stop_evt.is_set():
            if not self.enabled:
                time.sleep(0.1)
                continue

            # intentar (re)abrir si no hay serial
            if self._ser is None:
                self._open_serial()

            line = self._read_serial_line()
            if line:
                _log.debug("Serial line: %s", line)
                v = self._parse_moist_from_line(line)
                if v is not None:
                    self.soil_moisture = v
                    self.last_soil_ts = time.time()
                    _log.info("Soil moisture actualizado desde serial: %d%%", v)
                else:
                    _log.debug("Linea serial sin soil_moisture: %s", line)
            else:
                # si no hay lectura, NO emulamos soil_moisture (se mantiene valor previo o None)
                pass

            # actualizar temperatura y humedad de aire
            self._tick_env_randoms()

            time.sleep(0.5)

        self._close_serial()

    def start(self):
        if self.thread and self.thread.is_alive():
            self.enabled = True
            return
        self.stop_evt.clear()
        self.enabled = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        _log.info("SensorManager iniciado (esperando lecturas serial JSON para soil_moisture).")

    def stop(self):
        self.enabled = False

    def get_payload(self):
        return {
            "soil_type": self.soil_type,
            "temperature": round(self.temperature, 1),
            "soil_moisture": (int(self.soil_moisture) if self.soil_moisture is not None else None),
            "air_humidity": int(self.air_humidity),
        }

    def set_soil_type(self, s: str):
        self.soil_type = s or "Desconocido"

# instancia compartida
sensors = SensorManager()

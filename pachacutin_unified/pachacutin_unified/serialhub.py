import threading, queue, time, serial, os
from . import config

class SerialHub:
    def __init__(self, serial_path=None, baud=None):
        self.serial_path = serial_path  # None = autodetect
        self.baud = baud or config.DEFAULT_BAUD
        self._thread = None
        self._stop = threading.Event()
        self._writer_q = queue.Queue()
        self._on_line = None
        self.is_running = False
        self._ser = None

    # ---- API ----
    def start(self):
        if self.is_running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.is_running = True

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        try:
            if self._ser:
                self._ser.close()
        except:
            pass
        self.is_running = False

    def set_callback(self, fn):
        self._on_line = fn

    def send(self, cmd):
        self._writer_q.put(str(cmd).strip() + '\n')

    # ---- Internos ----
    def _find_device(self):
        # prefer /dev/serial/by-id (estable)
        byid = '/dev/serial/by-id'
        if os.path.isdir(byid):
            cands = sorted(os.listdir(byid))
            for name in cands:
                if 'Arduino' in name or 'arduino' in name:
                    return os.path.join(byid, name)
            # si no, toma el primero disponible
            if cands:
                return os.path.join(byid, cands[0])

        # fallback rápido
        for dev in ['/dev/ttyACM0','/dev/ttyUSB0','/dev/ttyACM1','/dev/ttyUSB1']:
            if os.path.exists(dev):
                return dev
        return None

    def _run(self):
        while not self._stop.is_set():
            dev = self.serial_path or self._find_device()
            if not dev:
                time.sleep(1.5)
                continue
            try:
                self._ser = serial.Serial(dev, self.baud, timeout=1)
                # bucle principal
                while not self._stop.is_set():
                    # escritura
                    try:
                        out = self._writer_q.get_nowait()
                        self._ser.write(out.encode('utf-8'))
                        self._ser.flush()
                    except Exception:
                        pass
                    # lectura
                    try:
                        line = self._ser.readline().decode(errors='ignore').strip()
                        if line and self._on_line:
                            try:
                                self._on_line(line)
                            except Exception:
                                pass
                    except Exception:
                        pass
                try:
                    self._ser.close()
                except:
                    pass
            except Exception:
                time.sleep(1.5)

import threading, time, serial
from .utils import find_serial_device

class SerialWriter:
    def __init__(self, cmd_queue, serial_path=None, baud=115200, reconnect_sleep=2.0):
        self.cmd_queue = cmd_queue
        self.serial_path = serial_path
        self.baud = baud
        self.reconnect_sleep = reconnect_sleep
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stop = threading.Event()

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2.0)

    def _open_serial(self, path):
        try:
            ser = serial.Serial(path, self.baud, timeout=1)
            return ser
        except Exception as e:
            print('Failed to open serial', path, e)
            return None

    def _run(self):
        ser = None
        while not self._stop.is_set():
            if ser is None:
                path = self.serial_path or find_serial_device()
                if not path:
                    print('No serial device found, retrying in', self.reconnect_sleep, 's')
                    time.sleep(self.reconnect_sleep)
                    continue
                ser = self._open_serial(path)
                if ser:
                    print('Serial opened on', path)
                else:
                    time.sleep(self.reconnect_sleep)
                    continue
            try:
                # bloquea esperando comando
                cmd = self.cmd_queue.get(timeout=1.0)
            except Exception:
                cmd = None
            if cmd is None:
                continue
            try:
                out = (str(cmd).strip() + '\n').encode('utf-8')
                ser.write(out)
                ser.flush()
                print('Sent to Arduino:', out)
            except Exception as e:
                print('Error writing to serial:', e)
                try:
                    ser.close()
                except:
                    pass
                ser = None
                time.sleep(self.reconnect_sleep)

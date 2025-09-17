import threading, queue, time

class GatewayModule:
    def __init__(self, serialhub=None):
        self.serialhub = serialhub
        self._q = queue.Queue()
        self._thread = None
        self._stop = threading.Event()
        self.is_running = False

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
        self.is_running = False

    def send(self, cmd):
        self._q.put(cmd)

    def _run(self):
        while not self._stop.is_set():
            try:
                cmd = self._q.get(timeout=1.0)
            except Exception:
                continue
            if self.serialhub:
                try:
                    self.serialhub.send(cmd)
                except Exception as e:
                    print('Gateway send error:', e)
            time.sleep(0.01)

import threading, subprocess, os, time

class CamModule:
    def __init__(self, server_path=None):
        self.server_path = server_path or os.environ.get('UNIFIED_USB_CAM_PATH')
        self.proc = None
        self.thread = None
        self._stop = threading.Event()
        self.is_running = False

    def start(self):
        if self.is_running:
            return
        self._stop.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.is_running = True

    def stop(self):
        self._stop.set()
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=2)
            except Exception:
                pass
        if self.thread:
            self.thread.join(timeout=2.0)
        self.is_running = False

    def _run(self):
        if not self.server_path:
            print('CamModule: no server_path configured')
            return
        # try common entrypoints
        for entry in ('run.py','app.py','server.py'):
            candidate = os.path.join(self.server_path, entry)
            if os.path.exists(candidate):
                try:
                    self.proc = subprocess.Popen(['python3', candidate], cwd=self.server_path)
                    time.sleep(2)
                    if self.proc.poll() is None:
                        print('CamModule started', candidate)
                        break
                except Exception as e:
                    print('CamModule start error', e)
        # keep alive until stop
        while not self._stop.is_set():
            time.sleep(1)

    def capture(self):
        # If usb_cam_server writes captures to static/captures, find the latest file
        captures_dir = os.path.join(self.server_path or '.', 'static', 'captures')
        if not os.path.isdir(captures_dir):
            return (False, 'captures dir not found: ' + captures_dir)
        files = sorted([f for f in os.listdir(captures_dir) if not f.startswith('.')])
        if not files:
            return (False, 'no images found')
        latest = files[-1]
        return (True, os.path.join('static','captures', latest))

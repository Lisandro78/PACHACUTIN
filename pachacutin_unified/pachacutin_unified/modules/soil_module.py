import threading, time, os

class SoilModule:
    def __init__(self, watch_dir=None):
        self.watch_dir = watch_dir or os.path.join(os.getcwd(), 'static', 'captures')
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
        if self.thread:
            self.thread.join(timeout=2.0)
        self.is_running = False

    def _run(self):
        seen = set(os.listdir(self.watch_dir)) if os.path.isdir(self.watch_dir) else set()
        while not self._stop.is_set():
            try:
                now = set(os.listdir(self.watch_dir)) if os.path.isdir(self.watch_dir) else set()
                new = now - seen
                for f in sorted(new):
                    path = os.path.join(self.watch_dir, f)
                    print('SoilModule: new capture', path)
                    # Here you can import your soil classifier and call it.
                    # Example (if available):
                    try:
                        import importlib, sys
                        sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
                        mod = importlib.import_module('soil_classifier.infer')
                        if hasattr(mod, 'predict'):
                            res = mod.predict(path)
                            print('Soil predict:', res)
                    except Exception as e:
                        print('SoilModule: classifier not available', e)
                    seen.add(f)
                time.sleep(1)
            except Exception as e:
                print('SoilModule error', e)
                time.sleep(1)

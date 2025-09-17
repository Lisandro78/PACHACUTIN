import threading, time
from collections import defaultdict

class ModuleManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._modules = {}
        self._active = set()
        self._sensor_data = {}
        self._init_modules()

    def _init_modules(self):
        # Lazy imports to avoid hard failures if module missing
        try:
            from .serialhub import SerialHub
            self._modules['serialhub'] = SerialHub()
        except Exception as e:
            print('Warning: SerialHub not available:', e)
            self._modules['serialhub'] = None
        try:
            from .modules.sensor_module import SensorModule
            self._modules['sensors'] = SensorModule(self._on_sensor_update, self._modules.get('serialhub'))
        except Exception as e:
            print('SensorModule not available:', e)
            self._modules['sensors'] = None
        try:
            from .modules.gateway_module import GatewayModule
            self._modules['control'] = GatewayModule(self._modules.get('serialhub'))
        except Exception as e:
            print('GatewayModule not available:', e)
            self._modules['control'] = None
        try:
            from .modules.cam_module import CamModule
            self._modules['monitor'] = CamModule()
        except Exception as e:
            print('CamModule not available:', e)
            self._modules['monitor'] = None
        try:
            from .modules.soil_module import SoilModule
            self._modules['soil'] = SoilModule()
        except Exception as e:
            print('SoilModule not available:', e)
            self._modules['soil'] = None

    def _on_sensor_update(self, data):
        with self._lock:
            self._sensor_data = dict(data)
            self._sensor_data['ts'] = time.strftime('%Y%m%d%H%M%S')

    def get_sensor_data(self):
        with self._lock:
            return dict(self._sensor_data)

    def is_active(self, key):
        return key in self._active

    def set_mode(self, mode):
        with self._lock:
            # stop all others except serialhub (serialhub can remain running)
            for k in list(self._active):
                if k != mode:
                    self._stop_module(k)
            # start requested module
            mod = self._modules.get(mode)
            if mod is None:
                return {'ok': False, 'error': f'module {mode} not available'}
            self._start_module(mode)
            return {'ok': True, 'mode': mode}

    def _start_module(self, key):
        mod = self._modules.get(key)
        if mod and not getattr(mod, 'is_running', False):
            # ensure serialhub is started before modules that use it
            if key in ('sensors','control') and self._modules.get('serialhub') is not None:
                self._modules['serialhub'].start()
            mod.start()
            self._active.add(key)
            print('Module', key, 'started')

    def _stop_module(self, key):
        mod = self._modules.get(key)
        if mod and getattr(mod, 'is_running', False):
            mod.stop()
            print('Module', key, 'stopped')
        self._active.discard(key)
        # if no serial-using modules active, stop serialhub
        if 'sensors' not in self._active and 'control' not in self._active:
            if self._modules.get('serialhub') is not None:
                self._modules['serialhub'].stop()

    def stop_all(self):
        with self._lock:
            for k in list(self._active):
                self._stop_module(k)

    def send_to_gateway(self, cmd):
        mod = self._modules.get('control')
        if mod:
            mod.send(cmd)
        else:
            raise RuntimeError('gateway module not available')

    def capture_image(self):
        mod = self._modules.get('monitor')
        if mod and getattr(mod,'is_running', False):
            return mod.capture()
        return (False, 'monitor not active')

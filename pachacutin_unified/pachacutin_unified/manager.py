import threading, time
from . import config

class ModuleManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._active = set()
        self._sensor_data = {}

        # Instancias de módulos (lazy-friendly)
        from .serialhub import SerialHub
        self._serialhub = SerialHub(serial_path=None, baud=config.DEFAULT_BAUD)

        # Módulos
        try:
            from .modules.sensor_module import SensorModule
            self._sensor_module = SensorModule(self._on_sensor_update, self._serialhub, baud=config.DEFAULT_BAUD)
        except Exception as e:
            print("SensorModule not available:", e); self._sensor_module = None

        try:
            from .modules.gateway_module import GatewayModule
            self._gateway_module = GatewayModule(self._serialhub)
        except Exception as e:
            print("GatewayModule not available:", e); self._gateway_module = None

        try:
            from .modules.cam_module import CamModule
            self._cam_module = CamModule()
        except Exception as e:
            print("CamModule not available:", e); self._cam_module = None

        try:
            from .modules.soil_module import SoilModule
            self._soil_module = SoilModule()
        except Exception as e:
            print("SoilModule not available:", e); self._soil_module = None

    # ---------- Hooks ----------
    def _on_sensor_update(self, data):
        with self._lock:
            d = dict(data) if data else {}
            d['ts'] = time.strftime('%Y%m%d%H%M%S')
            self._sensor_data = d

    # ---------- API ----------
    def get_sensor_data(self):
        with self._lock:
            return dict(self._sensor_data)

    def is_active(self, key):
        return key in self._active

    def set_mode(self, mode):
        # Apaga todo menos el requerido
        for k in list(self._active):
            if k != mode:
                self._stop_module(k)
        # Enciende el solicitado
        self._start_module(mode)
        return {'ok': True, 'mode': mode}

    def stop_all(self):
        for k in list(self._active):
            self._stop_module(k)

    def send_to_gateway(self, cmd):
        if self._gateway_module:
            self._gateway_module.send(cmd)
        else:
            raise RuntimeError("gateway module not available")

    def capture_image(self):
        if self._cam_module and getattr(self._cam_module, 'is_running', False):
            return self._cam_module.capture()
        return (False, 'monitor not active')

    # ---------- Internos ----------
    def _start_module(self, key):
        if key == 'sensors' and self._sensor_module:
            self._serialhub.start()
            self._sensor_module.start()
            self._active.add('sensors')
            print('Module sensors started')
        elif key == 'control' and self._gateway_module:
            self._serialhub.start()
            self._gateway_module.start()
            self._active.add('control')
            print('Module control started')
        elif key == 'monitor' and self._cam_module:
            self._cam_module.start()
            self._active.add('monitor')
            print('Module monitor started')
        elif key == 'soil' and self._soil_module:
            self._soil_module.start()
            self._active.add('soil')
            print('Module soil started')

    def _stop_module(self, key):
        if key == 'sensors' and self._sensor_module and self._sensor_module.is_running:
            self._sensor_module.stop()
            self._active.discard('sensors')
            print('Module sensors stopped')
        elif key == 'control' and self._gateway_module and self._gateway_module.is_running:
            self._gateway_module.stop()
            self._active.discard('control')
            print('Module control stopped')
        elif key == 'monitor' and self._cam_module and self._cam_module.is_running:
            self._cam_module.stop()
            self._active.discard('monitor')
            print('Module monitor stopped')
        elif key == 'soil' and self._soil_module and self._soil_module.is_running:
            self._soil_module.stop()
            self._active.discard('soil')
            print('Module soil stopped')

        # Cierra serial si ni sensors ni control están activos
        if 'sensors' not in self._active and 'control' not in self._active:
            self._serialhub.stop()

import threading, time, json

class SensorModule:
    def __init__(self, update_cb, serialhub=None, baud=115200):
        self.update_cb = update_cb
        self.serialhub = serialhub
        self.baud = baud
        self.is_running = False

    def start(self):
        if self.is_running:
            return
        # register callback to serialhub
        if self.serialhub:
            self.serialhub.set_callback(self._on_line)
        self.is_running = True

    def stop(self):
        if self.serialhub:
            self.serialhub.set_callback(None)
        self.is_running = False

    def _on_line(self, line):
        # try JSON
        try:
            data = json.loads(line)
        except Exception:
            data = {}
            # try k:v,k2:v2
            for part in line.split(','):
                if ':' in part:
                    k,v = part.split(':',1)
                    k=k.strip(); v=v.strip()
                    try:
                        v = float(v) if '.' in v else int(v)
                    except:
                        pass
                    data[k] = v
        # normalize keys to what AppInventor expects
        normalized = {}
        if 'soil_type' in data: normalized['soil_type']=data.get('soil_type')
        if 'temperature' in data: normalized['temperature']=data.get('temperature')
        if 'soil_moisture' in data: normalized['soil_moisture']=data.get('soil_moisture')
        if 'air_humidity' in data: normalized['air_humidity']=data.get('air_humidity')
        # also accept alternative keys
        if 'temp' in data and 'temperature' not in normalized: normalized['temperature']=data.get('temp')
        if 'soil' in data and 'soil_type' not in normalized: normalized['soil_type']=data.get('soil')
        # pass to manager
        self.update_cb(normalized)

# pachacutin_ai/app/arduino_reader.py
import serial, json, time

_ser = None

def _ensure_serial():
    global _ser
    if _ser is None:
        _ser = serial.Serial("/dev/ttyACM0", 9600, timeout=2)
        time.sleep(2)
    return _ser

def read_arduino():
    try:
        ser = _ensure_serial()
        for _ in range(3):
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                print("⚠️ Línea malformada (ignorada):", line)
        return None
    except Exception as e:
        print("⚠️ Error leyendo Arduino:", e)
        return None

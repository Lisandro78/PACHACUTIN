import os

def find_serial_device():
    # Busca en /dev/serial/by-id por nombres con Arduino o ACM/USB conocidos
    byid = '/dev/serial/by-id'
    if os.path.isdir(byid):
        for name in os.listdir(byid):
            if 'Arduino' in name or 'arduino' in name or 'USB' in name:
                return os.path.join(byid, name)
    # fallbacks comunes
    for dev in ['/dev/ttyACM0', '/dev/ttyUSB0', '/dev/ttyACM1', '/dev/ttyUSB1']:
        if os.path.exists(dev):
            return dev
    return None

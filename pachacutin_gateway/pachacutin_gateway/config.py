import os

# HTTP server
HTTP_PORT = int(os.environ.get('PG_HTTP_PORT', 5000))

# Serial defaults
SERIAL_PATH = os.environ.get('PG_SERIAL_PATH', None)  # si None, se detecta automáticamente
BAUD = int(os.environ.get('PG_BAUD', 115200))
SERIAL_RECONNECT_S = float(os.environ.get('PG_SERIAL_RECONNECT_S', 2.0))

# Seguridad simple (token)
AUTH_TOKEN = os.environ.get('PG_AUTH_TOKEN', 'mi_token_local')

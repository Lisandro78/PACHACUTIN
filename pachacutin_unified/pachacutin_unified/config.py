import os
HTTP_PORT = int(os.environ.get('UNIFIED_HTTP_PORT', 5000))
AUTH_TOKEN = os.environ.get('UNIFIED_AUTH_TOKEN', 'mi_token_local')
DEFAULT_BAUD = int(os.environ.get('UNIFIED_BAUD', 115200))
USB_CAM_SERVER_PATH = os.environ.get('UNIFIED_USB_CAM_PATH', '../usb_cam_server')
SOIL_CLASSIFIER_PATH = os.environ.get('UNIFIED_SOIL_PATH', '../soil_classifier')
# Timeouts
MODE_START_TIMEOUT_S = float(os.environ.get('UNIFIED_MODE_TIMEOUT', 8.0))

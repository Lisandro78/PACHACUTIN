# -*- coding: utf-8 -*-
import os

# Servidor
HOST  = os.environ.get("PACHACUTIN_HOST", "0.0.0.0")
PORT  = int(os.environ.get("PACHACUTIN_PORT", "5000"))
DEBUG = os.environ.get("PACHACUTIN_DEBUG", "1") == "1"

# Seguridad simple
TOKEN = os.environ.get("PACHACUTIN_TOKEN", "pachacutin2025")

# Rutas de archivos
BASE_DIR    = os.path.dirname(__file__)
STATIC_DIR  = os.path.join(BASE_DIR, "static")
CAPTURE_DIR = os.path.join(STATIC_DIR, "captures")
os.makedirs(CAPTURE_DIR, exist_ok=True)

# Cámara
CAM_INDEX = os.environ.get("PACHACUTIN_CAM_INDEX")  # "0","1","2"... o None
CAM_TRY_INDICES = [0,1,2,3]

# Serial (Arduino)
SERIAL_PORT = os.environ.get("PACHACUTIN_SERIAL", "/dev/ttyACM0").strip()   # p.ej. /dev/ttyACM0
SERIAL_BAUD = int(os.environ.get("PACHACUTIN_BAUD", "9600"))

# OpenAI (opcional)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL   = os.environ.get("OPENAI_MODEL", "gpt-4o-nano")

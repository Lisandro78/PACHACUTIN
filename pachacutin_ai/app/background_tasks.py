import threading
import time
import random

from pachacutin_ai.app.arduino_reader import read_arduino

# ====== (opcional) cámara / modelo ======
import torch
import cv2
from torchvision import transforms
from PIL import Image
from soil_classifier.model import get_model
from soil_classifier.dataset import load_data

# ---------- Estado compartido ----------
latest_soil = {"soil_moisture": 40.0, "ts_soil": None}
latest_weather = {"temperatura": 16.0, "humedad_aire": 90.0, "ts_weather": None}
latest_soil_type = "Desconocido"
lock = threading.Lock()

# ---------- Modelo de suelo (opcional) ----------
MODEL_PATH = "soil_classifier/soil_model.pth"
DATA_DIR = "/home/robotica/Soil-Classification-Dataset/Orignal-Dataset"

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
try:
    _, _, classes = load_data(DATA_DIR)
    model = get_model(len(classes))
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model = model.to(device)
    model.eval()
    MODEL_OK = True
except Exception as e:
    print("⚠️ No se cargó el modelo de cámara:", e)
    classes, model, MODEL_OK = [], None, False


# ---------- Hilos de actualización (5 s) ----------
def update_arduino():
    while True:
        data = read_arduino() or {}
        val = data.get("soil_moisture")
        if val is None:
            val = random.randint(20, 60)
        try:
            val = float(val)
        except Exception:
            val = 40.0
        with lock:
            latest_soil["soil_moisture"] = val
            latest_soil["ts_soil"] = time.time()
        print(f"[ARDUINO] soil_moisture={val} @ {time.strftime('%H:%M:%S')}")
        time.sleep(5)

def update_weather():
    while True:
        temperatura = round(random.uniform(14, 19), 2)
        humedad_aire = round(random.uniform(80, 100), 2)
        with lock:
            latest_weather["temperatura"] = temperatura
            latest_weather["humedad_aire"] = humedad_aire
            latest_weather["ts_weather"] = time.time()
        print(f"[WEATHER] T={temperatura}°C H={humedad_aire}% @ {time.strftime('%H:%M:%S')}")
        time.sleep(5)

def update_camera():
    if not MODEL_OK:
        # Sin modelo: solo marca desconocido cada 5 s
        while True:
            with lock:
                pass  # nada
            time.sleep(5)
        return

    cap = cv2.VideoCapture(0)
    try:
        while True:
            if not cap.isOpened():
                cap.open(0)
                time.sleep(0.5)
            ok, frame = cap.read()
            if not ok:
                with lock:
                    pass
                print(f"[CAM] sin frame @ {time.strftime('%H:%M:%S')}")
                time.sleep(5)
                continue

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            image = transform(image).unsqueeze(0).to(device)
            with torch.no_grad():
                outputs = model(image)
                _, preds = torch.max(outputs, 1)
            soil_type = classes[preds.item()]
            with lock:
                global latest_soil_type
                latest_soil_type = soil_type
            print(f"[CAM] soil_type={soil_type} @ {time.strftime('%H:%M:%S')}")
            time.sleep(5)
    finally:
        cap.release()

def start_background_tasks():
    threading.Thread(target=update_arduino, daemon=True).start()
    threading.Thread(target=update_weather, daemon=True).start()
    threading.Thread(target=update_camera, daemon=True).start()

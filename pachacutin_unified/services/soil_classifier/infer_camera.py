import cv2
import torch
from torchvision import transforms
from soil_classifier.model import get_model
from soil_classifier.dataset import load_data
from PIL import Image

# Configuración
MODEL_PATH = "soil_classifier/soil_model.pth"
DATA_DIR = "/home/robotica/Soil-Classification-Dataset/Orignal-Dataset"

# Preprocesamiento igual que en entrenamiento
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

# 🚀 Cargar modelo una sola vez
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_, _, classes = load_data(DATA_DIR)
model = get_model(len(classes))
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model = model.to(device)
model.eval()

def classify_soil():
    """Captura un solo frame de la cámara USB (/dev/video2) y devuelve el tipo de suelo detectado."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara en índice 2 (/dev/video2)")
        return None

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("⚠️ No se pudo leer frame de la cámara")
        return None

    # Preprocesar imagen
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)
    image = transform(image).unsqueeze(0).to(device)

    # Inferencia
    with torch.no_grad():
        outputs = model(image)
        probs = torch.nn.functional.softmax(outputs, dim=1)
        _, preds = torch.max(outputs, 1)

    predicted_class = classes[preds.item()]
    confidence = probs[0][preds.item()].item() * 100

    print(f"➡️ {predicted_class} ({confidence:.2f}%)")
    return predicted_class

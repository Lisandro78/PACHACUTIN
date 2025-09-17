import torch
from torchvision import transforms
from PIL import Image
from model import get_model

def predict_image(img_path, model_path, classes):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225])
    ])

    image = Image.open(img_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(device)

    model = get_model(len(classes))
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()

    with torch.no_grad():
        outputs = model(image)
        _, preds = torch.max(outputs, 1)
        predicted_class = classes[preds.item()]

    print(f"Predicción: {predicted_class}")
    return predicted_class

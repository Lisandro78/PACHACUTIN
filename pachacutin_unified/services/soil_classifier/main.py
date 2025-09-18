import argparse
from train import train_model
from evaluate import evaluate_model
from infer import predict_image
from dataset import load_data
from model import get_model
import torch

def main():
    parser = argparse.ArgumentParser(description="Soil Classification System")
    parser.add_argument("--train", action="store_true", help="Entrenar el modelo")
    parser.add_argument("--data", type=str, default="Soil-Classification-Dataset", help="Ruta al dataset")
    parser.add_argument("--epochs", type=int, default=5, help="Número de épocas de entrenamiento")
    parser.add_argument("--model", type=str, default="soil_model.pth", help="Ruta del modelo guardado")
    parser.add_argument("--infer", type=str, help="Imagen a clasificar")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if args.train:
        model, test_loader, classes = train_model(args.data, epochs=args.epochs, save_path=args.model)
        acc = evaluate_model(model, test_loader, device)
        print(f"Precisión final: {acc:.2f}%")

    elif args.infer:
        # cargamos las clases desde el dataset
        _, _, classes = load_data(args.data)
        predict_image(args.infer, args.model, classes)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()

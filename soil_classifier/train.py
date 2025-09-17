import torch
import torch.optim as optim
import torch.nn as nn
from dataset import load_data
from model import get_model

def train_model(data_dir, epochs=5, lr=0.001, batch_size=32, save_path="soil_model.pth"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_loader, test_loader, classes = load_data(data_dir, batch_size=batch_size)
    model = get_model(len(classes)).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()

        print(f"Epoch [{epoch+1}/{epochs}], Loss: {running_loss/len(train_loader):.4f}")

    torch.save(model.state_dict(), save_path)
    print(f"Modelo guardado en {save_path}")
    return model, test_loader, classes

if __name__ == "__main__":
    DATA_DIR = "/ruta/a/Soil-Classification-Dataset"
    train_model(DATA_DIR, epochs=5)

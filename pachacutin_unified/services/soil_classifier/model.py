import torch.nn as nn
import torchvision.models as models

def get_model(num_classes):
    # Usar la API moderna de TorchVision
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, num_classes)
    return model

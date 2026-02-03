
import torch
import torch.nn as nn
from torchvision import models

class HorseBreedClassifier(nn.Module):
    def __init__(self, num_classes, pretrained=True):
        super(HorseBreedClassifier, self).__init__()
        # Use EfficientNet B0 as per guide.md requirements
        self.model = models.efficientnet_b0(pretrained=pretrained)
        
        # Replace the classifier head
        # EfficientNet's classifier is a Sequential with a Dropout and Linear layer
        in_features = self.model.classifier[1].in_features
        self.model.classifier[1] = nn.Linear(in_features, num_classes)
        
    def forward(self, x):
        return self.model(x)

def load_model(model_path, num_classes, device):
    model = HorseBreedClassifier(num_classes=num_classes)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model

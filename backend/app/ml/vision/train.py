
import os
import copy
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from pathlib import Path

from dataset import HorseBreedsDataset, get_transforms
from model import HorseBreedClassifier

def train_model(data_dir, output_dir, num_epochs=25, batch_size=32, learning_rate=0.001):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Create dataset
    full_dataset = HorseBreedsDataset(data_dir, transform=get_transforms(is_training=True))
    num_classes = len(full_dataset.classes)
    class_names = full_dataset.classes
    print(f"Found {len(full_dataset)} images for {num_classes} classes: {class_names}")
    
    # Split dataset
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    # Reset transform for validation to be deterministic
    val_dataset.dataset.transform = get_transforms(is_training=False) 
    # Note: random_split wraps the dataset, so we might need to handle transforms carefully if we want different ones.
    # Actually, random_split shares the underlying dataset. 
    # To have different transforms, it's better to create two dataset instances with different transforms.
    
    # Proper split with transforms
    train_full_ds = HorseBreedsDataset(data_dir, transform=get_transforms(is_training=True))
    val_full_ds = HorseBreedsDataset(data_dir, transform=get_transforms(is_training=False))
    
    # Use indices from random_split to create subsets
    indices = torch.randperm(len(train_full_ds)).tolist()
    train_indices = indices[:train_size]
    val_indices = indices[train_size:]
    
    train_dataset = torch.utils.data.Subset(train_full_ds, train_indices)
    val_dataset = torch.utils.data.Subset(val_full_ds, val_indices)
    
    dataloaders = {
        'train': DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4),
        'val': DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=4)
    }
    dataset_sizes = {'train': len(train_dataset), 'val': len(val_dataset)}
    
    # Model Setup
    model = HorseBreedClassifier(num_classes=num_classes)
    model = model.to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.1)
    
    since = time.time()
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for epoch in range(num_epochs):
        print(f'Epoch {epoch}/{num_epochs - 1}')
        print('-' * 10)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
            
            if phase == 'train':
                scheduler.step()

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())
                torch.save(model.state_dict(), output_path / 'best_model.pth')

        print()

    time_elapsed = time.time() - since
    print(f'Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s')
    print(f'Best val Acc: {best_acc:4f}')

    # Load best model weights
    model.load_state_dict(best_model_wts)
    return model

if __name__ == "__main__":
    DATA_DIR = "d:/EquiVision/backend/data/raw/horse-breeds"
    OUTPUT_DIR = "d:/EquiVision/backend/app/ml/vision/weights"
    
    # Check if data exists
    if not os.path.exists(DATA_DIR):
        print(f"Data directory {DATA_DIR} not found due to previous steps not being fully automated or validated yet.")
    else:
        train_model(DATA_DIR, OUTPUT_DIR, num_epochs=10)

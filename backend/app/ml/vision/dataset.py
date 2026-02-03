
import os
import json
from pathlib import Path
from PIL import Image
import torch
from torch.utils.data import Dataset
from torchvision import transforms

class HorseBreedsDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        """
        Args:
            root_dir (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied on a sample.
        """
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.samples = []
        self.class_to_idx = {}
        self.classes = []
        
        # Load labels mapping
        labels_path = self.root_dir / "labels.json"
        if not labels_path.exists():
            raise FileNotFoundError(f"labels.json not found in {root_dir}")
            
        with open(labels_path, 'r') as f:
            self.id_to_name = json.load(f)
            
        # Create class mapping (name -> idx)
        # We sort to ensure consistent ordering
        self.classes = sorted(list(self.id_to_name.values()))
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}
        
        # Gather images
        # Filenames are like '01_001.png', where '01' is the breed ID
        for file_path in self.root_dir.glob("*.png"):
            breed_id = file_path.name.split('_')[0]
            if breed_id in self.id_to_name:
                breed_name = self.id_to_name[breed_id]
                self.samples.append((str(file_path), self.class_to_idx[breed_name]))
                
    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, target = self.samples[idx]
        image = Image.open(img_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, target

def get_transforms(img_size=224, is_training=True):
    if is_training:
        return transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    else:
        return transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

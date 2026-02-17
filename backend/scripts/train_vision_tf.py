import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from pathlib import Path

# --- CONFIGURATION ---
DATA_DIR = Path("data/clean/horse-breeds")
MODEL_DIR = Path("app/ml/vision/weights_tf")
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 30

# --- GPU/JIT/LAYOUT FIXES ---
os.environ["TF_XLA_FLAGS"] = "--tf_xla_auto_jit=-1"
os.environ["XLA_FLAGS"] = "--xla_gpu_jit=false"
os.environ["TF_DISABLE_LAYOUT_OPTIMIZER"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# Try to find libdevice on common Linux paths and inside the VENV packages
import site
paths_to_check = [
    "/usr/local/cuda/nvvm/libdevice",
    "/usr/lib/cuda/nvvm/libdevice",
    "/usr/lib/nvidia-cuda-toolkit/nvvm/libdevice"
]

# Add VENV paths
for s in site.getsitepackages() + [site.getusersitepackages()]:
    paths_to_check.append(os.path.join(s, "nvidia/cuda_nvcc/nvvm/libdevice"))

for path in paths_to_check:
    if os.path.exists(path):
        os.environ["XLA_FLAGS"] = f"--xla_gpu_cuda_data_dir={Path(path).parent.parent}"
        print(f"✅ Found CUDA libdevice at: {path}")
        break

def build_transfer_model(num_classes):
    """
    Standard Industry Practice: Use MobileNetV2 pre-trained on ImageNet.
    Much faster to train and much more accurate for small datasets.
    """
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3),
        include_top=False,
        weights='imagenet'
    )
    # Freeze the base model (don't train the early layers)
    base_model.trainable = False

    model = models.Sequential([
        layers.Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3)),
        layers.Rescaling(1./127.5, offset=-1), # MobileNetV2 expects [-1, 1]
        
        # Data Augmentation
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.1),
        layers.RandomZoom(0.1),

        base_model,
        layers.GlobalAveragePooling2D(),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(512, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])

    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'],
        jit_compile=False
    )
    return model

def train_tf_model():
    if not DATA_DIR.exists():
        print(f"Error: Clean data not found at {DATA_DIR}. Run clean_vision_data.py first.")
        return

    # Load labels
    labels_path = DATA_DIR / "labels.json"
    with open(labels_path, 'r') as f:
        breed_map = json.load(f)
    
    class_names = sorted(list(breed_map.values()))
    num_classes = len(class_names)
    print(f"Detected {num_classes} classes: {class_names}")

    # Load dataset using Keras utility
    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        labels='inferred',
        label_mode='int'
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        labels='inferred',
        label_mode='int'
    )

    # Performance optimization
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    # Build and Train
    print("\nBuilding MobileNetV2 Transfer Model...")
    model = build_transfer_model(num_classes)
    model.summary()

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(MODEL_DIR / "horse_vision_tf.h5"),
            save_best_only=True,
            monitor='val_accuracy',
            mode='max'
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.2,
            patience=3,
            min_lr=1e-6
        )
    ]

    print("\nStarting TensorFlow Training...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=callbacks
    )

    # Save final model
    model.save(str(MODEL_DIR / "horse_vision_tf_final.h5"))
    print(f"\nTraining Complete. Models saved to {MODEL_DIR}")

if __name__ == "__main__":
    train_tf_model()

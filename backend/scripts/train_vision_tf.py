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

def build_custom_cnn(num_classes):
    """
    As requested: Custom CNN with Conv2D filters, pooling, and dropout.
    Designed for 11 horse breeds.
    """
    model = models.Sequential([
        # Data Augmentation (built into the model for portability)
        layers.RandomFlip("horizontal", input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3)),
        layers.RandomRotation(0.1),
        layers.RandomZoom(0.1),
        layers.Rescaling(1./255),

        # Block 1
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),

        # Block 2
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),

        # Block 3
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),

        # Block 4
        layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.3),

        # Dense Head
        layers.Flatten(),
        layers.Dense(512, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])

    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
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
    print("\nBuilding Custom CNN...")
    model = build_custom_cnn(num_classes)
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

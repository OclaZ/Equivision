import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data/clean/horse-breeds-processed"
MODEL_DIR = BASE_DIR / "app/ml/vision/weights_tf_scraped"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 30

# --- GPU/JIT FIXES ---
os.environ["TF_XLA_FLAGS"] = "--tf_xla_auto_jit=-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

def build_transfer_model(num_classes):
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False

    model = models.Sequential([
        layers.Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3)),
        layers.Rescaling(1./127.5, offset=-1),
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
        metrics=['accuracy']
    )
    return model

def train_scraped_model():
    if not DATA_DIR.exists():
        print(f"Error: Clean data not found at {DATA_DIR}. Run process_scraped_images.py first.")
        return

    print("Loading dataset from folder structure...")
    
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

    class_names = train_ds.class_names
    num_classes = len(class_names)
    print(f"Detected {num_classes} classes: {class_names}")
    
    # Save class mapping for reference
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_DIR / "class_indices.json", "w") as f:
        json.dump({name: i for i, name in enumerate(class_names)}, f)

    # Optimization
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    # Build and Train
    print("\nBuilding MobileNetV2 Transfer Model...")
    model = build_transfer_model(num_classes)
    
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(MODEL_DIR / "horse_vision_scraped.h5"),
            save_best_only=True,
            monitor='val_accuracy',
            mode='max'
        ),
        tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    ]

    print("\nStarting TensorFlow Training...")
    
    # Optional Class Weights if sklearn is available
    class_weights_dict = None
    try:
        from sklearn.utils import class_weight
        print("Calculating class weights for imbalance handling...")
        y_train = []
        for images, labels in train_ds:
             y_train.extend(labels.numpy())
        
        unique_classes = np.unique(y_train)
        cw = class_weight.compute_class_weight('balanced', classes=unique_classes, y=np.array(y_train))
        class_weights_dict = dict(zip(unique_classes, cw))
        print(f"Class Weights Active: {class_weights_dict}")
    except ImportError:
        print("sklearn not found. Training without class weights.")

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        class_weight=class_weights_dict,
        callbacks=callbacks
    )

    model.save(str(MODEL_DIR / "horse_vision_scraped_final.h5"))
    print(f"\nTraining Complete. Models saved to {MODEL_DIR}")

if __name__ == "__main__":
    train_scraped_model()

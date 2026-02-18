import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data/clean/horse-breeds-processed"
MODEL_DIR = BASE_DIR / "app/ml/vision/weights_tf_scraped"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS_HEAD = 10
EPOCHS_FINE = 20

# --- GPU/JIT FIXES ---
os.environ["TF_XLA_FLAGS"] = "--tf_xla_auto_jit=-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

def build_model(num_classes):
    # Use EfficientNetV2B0 - State of the Art lightweight model
    base_model = tf.keras.applications.EfficientNetV2B0(
        input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False  # Freeze initially

    inputs = layers.Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3))
    
    # EfficientNet expects [0-255], it handles scaling internally!
    # But just to be safe, check docs. V2 usually expects raw.
    # We will use simple Augmentation layers.
    x = layers.RandomFlip("horizontal")(inputs)
    x = layers.RandomRotation(0.1)(x)
    x = layers.RandomZoom(0.1)(x)
    x = layers.RandomContrast(0.1)(x) # Added contrast

    x = base_model(x, training=False) 
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    
    # Robust Head
    x = layers.Dense(1024, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    outputs = layers.Dense(num_classes, activation='softmax')(x)

    model = models.Model(inputs, outputs)
    return model, base_model

def train_scraped_model():
    if not DATA_DIR.exists():
        print(f"Error: Clean data not found at {DATA_DIR}. Run process_scraped_images.py first.")
        return

    print("Loading dataset...")
    
    # Load with 'categorical' for label smoothing support
    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR, validation_split=0.2, subset="training", seed=123,
        image_size=IMG_SIZE, batch_size=BATCH_SIZE, label_mode='categorical'
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR, validation_split=0.2, subset="validation", seed=123,
        image_size=IMG_SIZE, batch_size=BATCH_SIZE, label_mode='categorical'
    )

    class_names = train_ds.class_names
    num_classes = len(class_names)
    print(f"Detected {num_classes} classes: {class_names}")
    
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_DIR / "class_indices.json", "w") as f:
        json.dump({name: i for i, name in enumerate(class_names)}, f)

    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    # --- STAGE 1: Train Head ---
    print("\n--- STAGE 1: Training Classification Head (Frozen Backbone) ---")
    model, base_model = build_model(num_classes)
    
    # Use Label Smoothing to prevent overconfidence
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-3),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=['accuracy']
    )

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(MODEL_DIR / "horse_vision_best.h5"),
            save_best_only=True, monitor='val_accuracy', mode='max'
        )
    ]

    history_head = model.fit(
        train_ds, validation_data=val_ds,
        epochs=EPOCHS_HEAD, callbacks=callbacks
    )

    # --- STAGE 2: Fine Tuning ---
    print("\n--- STAGE 2: Fine Tuning (Unfreezing Backbone) ---")
    base_model.trainable = True
    
    # We unfreeze all, but use a TINY learning rate.
    # EfficientNetV2 is deep, so we must be gentle.
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-5), # 100x smaller LR
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=['accuracy']
    )

    # Continue training
    total_epochs = EPOCHS_HEAD + EPOCHS_FINE
    
    history_fine = model.fit(
        train_ds, validation_data=val_ds,
        epochs=total_epochs,
        initial_epoch=history_head.epoch[-1] + 1,
        callbacks=callbacks
    )

    model.save(str(MODEL_DIR / "horse_vision_final.h5"))
    print(f"\nTraining Complete. Models saved to {MODEL_DIR}")

if __name__ == "__main__":
    train_scraped_model()

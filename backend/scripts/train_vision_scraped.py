import os
import json
import random
import shutil
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data/clean/horse-breeds-processed"
TRAIN_DIR = BASE_DIR / "data/clean/horse-breeds-training"
MODEL_DIR = BASE_DIR / "app/ml/vision/weights_tf_scraped"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32

# Breeds to KEEP (>=90 images + Barb exception)
KEEP_BREEDS = {
    "Akhal-Teke", "Andalusian", "Arabian", "Barb", "Friesian",
    "Hanoverian", "Holsteiner", "KWPN", "Lusitano", "Oldenburg",
    "Orlov_Trotter", "Paint_Horse", "Pony", "Quarter_Horse",
    "Selle_Français", "Trakehner", "Welsh", "Westphalian"
}
MAX_PER_CLASS = 300  # Cap large classes for balance

# --- GPU/JIT FIXES ---
os.environ["TF_XLA_FLAGS"] = "--tf_xla_auto_jit=-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

def prepare_balanced_data():
    """Create a balanced training directory from the clean data."""
    print("="*50)
    print("PREPARING BALANCED TRAINING DATA")
    print("="*50)
    
    if TRAIN_DIR.exists():
        shutil.rmtree(TRAIN_DIR)
    TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    
    total_kept = 0
    for breed_dir in sorted(DATA_DIR.iterdir()):
        if not breed_dir.is_dir():
            continue
        
        breed_name = breed_dir.name
        
        # Filter: only keep selected breeds
        if breed_name not in KEEP_BREEDS:
            print(f"  ❌ Skipping {breed_name}")
            continue
        
        images = list(breed_dir.glob("*.jpg"))
        original_count = len(images)
        
        # Cap large classes
        if len(images) > MAX_PER_CLASS:
            random.seed(42)  # Reproducible
            images = random.sample(images, MAX_PER_CLASS)
        
        # Copy to training directory
        target_dir = TRAIN_DIR / breed_name
        target_dir.mkdir(exist_ok=True)
        
        for img in images:
            shutil.copy2(img, target_dir / img.name)
        
        kept = len(images)
        total_kept += kept
        status = f"(capped {original_count}→{kept})" if original_count > MAX_PER_CLASS else ""
        print(f"  ✅ {breed_name}: {kept} images {status}")
    
    print(f"\nTotal: {total_kept} images across {len(KEEP_BREEDS)} breeds")
    return total_kept

def build_model(num_classes):
    base_model = tf.keras.applications.EfficientNetV2B0(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False

    inputs = layers.Input(shape=(*IMG_SIZE, 3))
    
    # Augmentation
    x = layers.RandomFlip("horizontal")(inputs)
    x = layers.RandomRotation(0.15)(x)
    x = layers.RandomZoom(0.15)(x)
    x = layers.RandomContrast(0.1)(x)

    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(512, activation='relu',
                     kernel_regularizer=tf.keras.regularizers.l2(1e-4))(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation='softmax')(x)

    return models.Model(inputs, outputs), base_model

def train():
    if not DATA_DIR.exists():
        print(f"Error: {DATA_DIR} not found. Run process_scraped_images.py first.")
        return

    # Step 1: Prepare balanced dataset
    prepare_balanced_data()

    # Step 2: Load data
    print("\nLoading dataset...")
    train_ds = tf.keras.utils.image_dataset_from_directory(
        TRAIN_DIR, validation_split=0.2, subset="training", seed=42,
        image_size=IMG_SIZE, batch_size=BATCH_SIZE, label_mode='categorical'
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        TRAIN_DIR, validation_split=0.2, subset="validation", seed=42,
        image_size=IMG_SIZE, batch_size=BATCH_SIZE, label_mode='categorical'
    )

    class_names = train_ds.class_names
    num_classes = len(class_names)
    print(f"\nTraining {num_classes} classes: {class_names}")
    
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_DIR / "class_indices.json", "w") as f:
        json.dump({name: i for i, name in enumerate(class_names)}, f)

    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    # Step 3: Build model
    print("\nBuilding EfficientNetV2B0...")
    model, base_model = build_model(num_classes)

    # ============================
    # STAGE 1: Train Head (15 epochs)
    # ============================
    print("\n" + "="*50)
    print("STAGE 1: Training Head (Backbone Frozen)")
    print("="*50)

    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-3),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=['accuracy']
    )

    stage1_cb = [
        callbacks.ModelCheckpoint(
            str(MODEL_DIR / "best.h5"),
            save_best_only=True, monitor='val_accuracy', mode='max'
        ),
        callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6, verbose=1
        ),
    ]

    h1 = model.fit(train_ds, validation_data=val_ds, epochs=15, callbacks=stage1_cb)

    # ============================
    # STAGE 2: Fine-Tune Top 30% (35 epochs)
    # ============================
    print("\n" + "="*50)
    print("STAGE 2: Fine-Tuning (Top 30% Unfrozen)")
    print("="*50)

    base_model.trainable = True
    num_layers = len(base_model.layers)
    freeze_until = int(num_layers * 0.7)
    for layer in base_model.layers[:freeze_until]:
        layer.trainable = False
    
    trainable = sum(1 for l in base_model.layers if l.trainable)
    frozen = sum(1 for l in base_model.layers if not l.trainable)
    print(f"Backbone: {frozen} frozen + {trainable} trainable layers")

    model.compile(
        optimizer=optimizers.Adam(learning_rate=5e-5),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=['accuracy']
    )

    stage2_cb = [
        callbacks.ModelCheckpoint(
            str(MODEL_DIR / "best.h5"),
            save_best_only=True, monitor='val_accuracy', mode='max'
        ),
        callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=3, min_lr=1e-7, verbose=1
        ),
        callbacks.EarlyStopping(
            monitor='val_loss', patience=8, restore_best_weights=True, verbose=1
        ),
    ]

    h2 = model.fit(
        train_ds, validation_data=val_ds,
        epochs=50, initial_epoch=h1.epoch[-1] + 1,
        callbacks=stage2_cb
    )

    # Save final model
    model.save(str(MODEL_DIR / "horse_vision_final.h5"))

    # Report
    best_val = max(h1.history['val_accuracy'] + h2.history['val_accuracy'])
    print(f"\n{'='*50}")
    print(f"TRAINING COMPLETE")
    print(f"Best Validation Accuracy: {best_val:.1%}")
    print(f"Classes: {num_classes}")
    print(f"Models saved to: {MODEL_DIR}")
    print(f"{'='*50}")

if __name__ == "__main__":
    train()

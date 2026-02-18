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
IMG_SIZE = (260, 260)
BATCH_SIZE = 32
MAX_PER_CLASS = 300

# Breed merging map: original_name -> merged_name
MERGE_MAP = {
    "Andalusian": "Iberian",
    "Lusitano": "Iberian",
    "Hanoverian": "Sport_Horse",
    "Holsteiner": "Sport_Horse",
    "KWPN": "Sport_Horse",
    "Oldenburg": "Sport_Horse",
    "Westphalian": "Sport_Horse",
}

# Individual breeds to keep (not merged)
KEEP_INDIVIDUAL = {
    "Akhal-Teke", "Arabian", "Barb", "Friesian", "Orlov_Trotter",
    "Paint_Horse", "Pony", "Quarter_Horse", "Selle_Français",
    "Trakehner", "Welsh"
}

# All breeds we use (individual + sources for merges)
ALL_SOURCE_BREEDS = KEEP_INDIVIDUAL | set(MERGE_MAP.keys())

os.environ["TF_XLA_FLAGS"] = "--tf_xla_auto_jit=-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# =====================
# MixUp (fixed: uses tf.random, not np.random)
# =====================
def mixup(dataset, alpha=0.2):
    ds2 = dataset.shuffle(2000)
    zipped = tf.data.Dataset.zip((dataset, ds2))

    def _apply(batch1, batch2):
        imgs1, lbls1 = batch1
        imgs2, lbls2 = batch2
        # Sample from Beta via Gamma trick
        g1 = tf.random.gamma([], alpha)
        g2 = tf.random.gamma([], alpha)
        lam = g1 / (g1 + g2 + 1e-8)
        lam = tf.maximum(lam, 1.0 - lam)  # Keep >= 0.5
        lam = tf.cast(lam, tf.float32)
        images = lam * imgs1 + (1.0 - lam) * imgs2
        labels = lam * lbls1 + (1.0 - lam) * lbls2
        return images, labels

    return zipped.map(_apply, num_parallel_calls=tf.data.AUTOTUNE)

def prepare_balanced_data():
    print("=" * 50)
    print("PREPARING BALANCED + MERGED TRAINING DATA")
    print("=" * 50)

    if TRAIN_DIR.exists():
        shutil.rmtree(TRAIN_DIR)
    TRAIN_DIR.mkdir(parents=True, exist_ok=True)

    # Collect all images per target class
    class_images = {}

    for breed_dir in sorted(DATA_DIR.iterdir()):
        if not breed_dir.is_dir():
            continue
        name = breed_dir.name

        if name not in ALL_SOURCE_BREEDS:
            print(f"  ❌ {name}")
            continue

        # Determine target class
        target = MERGE_MAP.get(name, name)
        imgs = list(breed_dir.glob("*.jpg"))

        if target not in class_images:
            class_images[target] = []
        class_images[target].extend(imgs)
        print(f"  📁 {name} ({len(imgs)} imgs) → {target}")

    # Now copy with capping
    print(f"\n--- Merged Classes ---")
    total = 0
    for cls_name, imgs in sorted(class_images.items()):
        original_count = len(imgs)

        if len(imgs) > MAX_PER_CLASS:
            random.seed(42)
            imgs = random.sample(imgs, MAX_PER_CLASS)

        dst = TRAIN_DIR / cls_name
        dst.mkdir(exist_ok=True)
        for img in imgs:
            # Use unique name to avoid overwrites from merged breeds
            new_name = f"{img.parent.name}_{img.name}"
            shutil.copy2(img, dst / new_name)

        kept = len(imgs)
        total += kept
        tag = f"(capped {original_count}→{kept})" if original_count > MAX_PER_CLASS else ""
        print(f"  ✅ {cls_name}: {kept} images {tag}")

    num_classes = len(class_images)
    print(f"\nTotal: {total} images across {num_classes} classes\n")
    return total, num_classes

def build_model(num_classes):
    base = tf.keras.applications.EfficientNetV2B0(
        input_shape=(*IMG_SIZE, 3), include_top=False, weights='imagenet'
    )
    base.trainable = False

    inp = layers.Input(shape=(*IMG_SIZE, 3))
    x = layers.RandomFlip("horizontal")(inp)
    x = layers.RandomRotation(0.15)(x)
    x = layers.RandomZoom(0.15)(x)
    x = layers.RandomContrast(0.1)(x)

    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.5)(x)
    x = layers.Dense(256, activation='relu',
                     kernel_regularizer=tf.keras.regularizers.l2(1e-3))(x)
    x = layers.Dropout(0.3)(x)
    out = layers.Dense(num_classes, activation='softmax')(x)

    return models.Model(inp, out), base

def train():
    if not DATA_DIR.exists():
        print(f"Error: {DATA_DIR} not found.")
        return

    total_imgs, num_cls = prepare_balanced_data()
    steps_per_epoch = total_imgs * 8 // (10 * BATCH_SIZE)  # 80% train split

    print("Loading dataset...")
    _tmp = tf.keras.utils.image_dataset_from_directory(
        TRAIN_DIR, validation_split=0.2, subset="training", seed=42,
        image_size=IMG_SIZE, batch_size=BATCH_SIZE, label_mode='categorical'
    )
    class_names = _tmp.class_names
    train_ds = _tmp.unbatch().batch(BATCH_SIZE, drop_remainder=True)

    val_ds = tf.keras.utils.image_dataset_from_directory(
        TRAIN_DIR, validation_split=0.2, subset="validation", seed=42,
        image_size=IMG_SIZE, batch_size=BATCH_SIZE, label_mode='categorical'
    )

    num_classes = len(class_names)
    print(f"Training {num_classes} classes: {class_names}\n")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_DIR / "class_indices.json", "w") as f:
        json.dump({name: i for i, name in enumerate(class_names)}, f)

    AUTOTUNE = tf.data.AUTOTUNE
    train_mix = mixup(train_ds.cache(), alpha=0.2).prefetch(AUTOTUNE)
    val_ds = val_ds.cache().prefetch(AUTOTUNE)

    model, base = build_model(num_classes)

    # ========== STAGE 1: Head Only (20 epochs) ==========
    print("=" * 50)
    print(f"STAGE 1: Training Head — {num_classes} classes, {steps_per_epoch} steps/epoch")
    print("=" * 50)

    model.compile(
        optimizer=optimizers.Adam(1e-3),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=['accuracy']
    )

    s1_cb = [
        callbacks.ModelCheckpoint(str(MODEL_DIR / "best.h5"),
                                  save_best_only=True, monitor='val_accuracy', mode='max'),
        callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3,
                                    min_lr=1e-6, verbose=1),
    ]

    h1 = model.fit(train_mix, validation_data=val_ds, epochs=20, callbacks=s1_cb)

    # ========== STAGE 2: Fine-Tune Top 40% ==========
    print("\n" + "=" * 50)
    print("STAGE 2: Fine-Tuning Top 40% of Backbone")
    print("=" * 50)

    base.trainable = True
    freeze_until = int(len(base.layers) * 0.6)
    for layer in base.layers[:freeze_until]:
        layer.trainable = False

    trainable = sum(1 for l in base.layers if l.trainable)
    frozen = sum(1 for l in base.layers if not l.trainable)
    print(f"Backbone: {frozen} frozen + {trainable} trainable\n")

    cosine_schedule = tf.keras.optimizers.schedules.CosineDecay(
        initial_learning_rate=1e-4,
        decay_steps=40 * steps_per_epoch,
        alpha=1e-7
    )

    model.compile(
        optimizer=optimizers.Adam(cosine_schedule),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=['accuracy']
    )

    s2_cb = [
        callbacks.ModelCheckpoint(str(MODEL_DIR / "best.h5"),
                                  save_best_only=True, monitor='val_accuracy', mode='max'),
        callbacks.EarlyStopping(monitor='val_accuracy', patience=12,
                                restore_best_weights=True, verbose=1),
    ]

    h2 = model.fit(train_mix, validation_data=val_ds,
                   epochs=60, initial_epoch=h1.epoch[-1] + 1,
                   callbacks=s2_cb)

    model.save(str(MODEL_DIR / "horse_vision_final.h5"))

    best = max(h1.history['val_accuracy'] + h2.history['val_accuracy'])
    print(f"\n{'=' * 50}")
    print(f"TRAINING COMPLETE")
    print(f"Best Validation Accuracy: {best:.1%}")
    print(f"Classes: {num_classes} → {class_names}")
    print(f"Model: {MODEL_DIR}")
    print(f"{'=' * 50}")

if __name__ == "__main__":
    train()

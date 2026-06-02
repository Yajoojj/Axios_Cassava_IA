"""Model helpers for cassava blight detection."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image
import tensorflow as tf


def build_model(input_shape: Tuple[int, int, int] = (224, 224, 3)) -> tf.keras.Model:
    base_model = tf.keras.applications.EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_shape=input_shape,
    )
    base_model.trainable = False

    inputs = tf.keras.Input(shape=input_shape)
    x = tf.keras.applications.efficientnet.preprocess_input(inputs)
    x = base_model(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid")(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model


def _load_model_from_ascii_path(model_path: str) -> tf.keras.Model:
    try:
        model_path.encode("ascii")
        return tf.keras.models.load_model(model_path, compile=False)
    except UnicodeEncodeError:
        suffix = Path(model_path).suffix or ".h5"
        with tempfile.NamedTemporaryFile(prefix="cassava_model_", suffix=suffix, delete=False) as tmp:
            temp_path = tmp.name
        try:
            shutil.copy2(model_path, temp_path)
            return tf.keras.models.load_model(temp_path, compile=False)
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass


def load_trained_model(model_path: str, allow_fallback: bool = True) -> Optional[tf.keras.Model]:
    if os.path.exists(model_path):
        return _load_model_from_ascii_path(model_path)
    if allow_fallback:
        return None
    return build_model()


def preprocess_image(image: Image.Image, target_size: Tuple[int, int] = (224, 224)) -> np.ndarray:
    if image.mode != "RGB":
        image = image.convert("RGB")
    resized = image.resize(target_size, Image.BILINEAR)
    arr = np.array(resized, dtype=np.float32)
    return np.expand_dims(arr, axis=0)

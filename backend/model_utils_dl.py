"""Utilitários de modelo para a detecção de bacteriose via EfficientNet.

Este módulo contém funções para construir a arquitetura da rede EfficientNet
para classificação binária (folha saudável vs. infectada), carregar um
modelo salvo em disco e pré‑processar imagens para uso com o modelo.
Os comentários foram escritos em português para facilitar a compreensão.
"""

from typing import Tuple
import os

import numpy as np
from PIL import Image
import tensorflow as tf


def build_model(input_shape: Tuple[int, int, int] = (224, 224, 3)) -> tf.keras.Model:
    """Cria e compila um modelo EfficientNet adaptado para classificação binária.

    O modelo base (EfficientNetB0) é importado com pesos pré‑treinados no ImageNet.
    As camadas da base são congeladas (não treináveis) por padrão. Em seguida,
    adicionamos camadas de pooling, dropout e uma camada densa final com ativação
    sigmoide para produzir uma única probabilidade de infecção.

    Args:
        input_shape: tupla indicando o formato de entrada das imagens
                     (altura, largura, canais). Recomenda‑se 224x224x3.

    Returns:
        Um objeto `tf.keras.Model` compilado pronto para treinamento ou inferência.
    """
    # Carrega o backbone EfficientNetB0 pré‑treinado
    base_model = tf.keras.applications.EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_shape=input_shape,
    )
    base_model.trainable = False  # Congela as camadas convolucionais

    inputs = tf.keras.Input(shape=input_shape)
    # Pré‑processamento específico da EfficientNet
    x = tf.keras.applications.efficientnet.preprocess_input(inputs)
    x = base_model(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid")(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs)

    # Compila o modelo para treinamento
    model.compile(
        optimizer=tf.keras.optimizers.Adam(),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model


def load_trained_model(model_path: str) -> tf.keras.Model:
    """Carrega um modelo salvo ou cria um novo se o arquivo não existir.

    Args:
        model_path: caminho para o arquivo `.h5` contendo o modelo Keras salvo.

    Returns:
        Modelo Keras carregado ou recém‑criado.

    Raises:
        Exception: Se houver erro ao carregar um modelo existente.
    """
    if os.path.exists(model_path):
        # Carrega o modelo existente com compilação
        model = tf.keras.models.load_model(model_path)
        return model
    else:
        # Caso não exista, cria um novo modelo vazio
        return build_model()


def preprocess_image(image: Image.Image, target_size: Tuple[int, int] = (224, 224)) -> np.ndarray:
    """Pré‑processa uma imagem PIL para o formato aceito pelo modelo.

    A função converte a imagem para RGB, redimensiona para `target_size`,
    normaliza os valores dos pixels para o intervalo [0, 1] e adiciona um
    eixo de batch.

    Args:
        image: instância de `PIL.Image` no modo RGB.
        target_size: tamanho de destino (largura, altura) para redimensionamento.

    Returns:
        Um array NumPy 4D de forma (1, altura, largura, 3) com valores
        normalizados.
    """
    # Assegura que a imagem está no modo RGB
    if image.mode != "RGB":
        image = image.convert("RGB")
    # Redimensiona para o tamanho desejado
    resized = image.resize(target_size, Image.BILINEAR)
    arr = np.array(resized, dtype=np.float32) / 255.0  # Normaliza para [0, 1]
    # Adiciona o eixo do batch
    return np.expand_dims(arr, axis=0)

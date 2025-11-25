"""Script de treinamento para o modelo EfficientNet na detecção de bacteriose.

Use este script para treinar um modelo a partir de um conjunto de dados
organizado em duas pastas: `healthy/` (folhas saudáveis) e `infected/`
(folhas com bacteriose). O script cria e treina um modelo EfficientNet
com pesos pré‑treinados e salva o modelo resultante em formato `.h5`.

Recomenda‑se executar este treinamento em uma máquina com GPU para
desempenho otimizado. Em sistemas sem GPU, o tempo de treinamento
pode ser significativamente maior.
"""

import argparse
import os

import tensorflow as tf

from model_utils_dl import build_model


def parse_args() -> argparse.Namespace:
    """Define e analisa os argumentos de linha de comando."""
    parser = argparse.ArgumentParser(description="Treinar modelo EfficientNet para detecção de bacteriose")
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Diretório contendo as subpastas 'healthy' e 'infected' com as imagens.",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Caminho para salvar o modelo treinado (exemplo: models/cassava_effnet.h5).",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=15,
        help="Número de épocas de treinamento (padrão: 15).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Tamanho do batch para treinamento (padrão: 32).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir
    model_path = args.model_path
    epochs = args.epochs
    batch_size = args.batch_size

    if not os.path.isdir(data_dir):
        raise ValueError(f"Diretório de dados '{data_dir}' não encontrado.")

    # Carrega datasets de treinamento e validação usando validação estratificada
    train_ds = tf.keras.preprocessing.image_dataset_from_directory(
        data_dir,
        labels="inferred",
        label_mode="binary",
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=(224, 224),
        batch_size=batch_size,
    )
    val_ds = tf.keras.preprocessing.image_dataset_from_directory(
        data_dir,
        labels="inferred",
        label_mode="binary",
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=(224, 224),
        batch_size=batch_size,
    )

    # Normaliza os pixels para o intervalo [0, 1]
    normalization_layer = tf.keras.layers.Rescaling(1.0 / 255.0)
    train_ds = train_ds.map(lambda x, y: (normalization_layer(x), y))
    val_ds = val_ds.map(lambda x, y: (normalization_layer(x), y))

    # Utiliza cache e prefetch para performance
    train_ds = train_ds.cache().prefetch(buffer_size=tf.data.AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=tf.data.AUTOTUNE)

    # Cria o modelo EfficientNet
    model = build_model((224, 224, 3))

    # Callbacks: parada antecipada e salvamento do melhor modelo
    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=5, restore_best_weights=True
    )
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        filepath=model_path,
        monitor="val_loss",
        save_best_only=True,
        verbose=1,
    )

    # Inicia o treinamento
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=[early_stop, checkpoint],
    )

    # Salva o modelo final após o treinamento (caso early_stop não salve a última epoch)
    model.save(model_path)
    print(f"Treinamento concluído. Modelo salvo em {model_path}")


if __name__ == "__main__":
    main()

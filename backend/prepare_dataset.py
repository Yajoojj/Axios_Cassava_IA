"""Script para organizar imagens mistas em pastas 'healthy' e 'infected'.

Este utilitário percorre um diretório contendo imagens de folhas misturadas
sem rótulo prévio (saudáveis ou infectadas) e, usando um modelo
treinado, calcula a probabilidade de cada imagem estar infectada. Com base
em um limiar definido pelo usuário, ele copia cada foto para uma pasta
correspondente (`healthy` ou `infected`) no diretório de saída.

IMPORTANTE: O script não apaga nem move os arquivos originais; apenas copia
para as pastas de destino. Após a classificação automática, recomenda‑se
revisar manualmente os resultados para corrigir eventuais erros antes de
usar o conjunto em treinamento.
"""

import argparse
import os
import shutil
from typing import List

from PIL import Image

from model_utils_dl import load_trained_model, preprocess_image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classificar imagens mistas em saudáveis e infectadas")
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Diretório contendo todas as imagens misturadas.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Diretório onde serão criadas as pastas 'healthy' e 'infected' com as imagens copiadas.",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Caminho para o modelo treinado (.h5) usado para classificar as imagens.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Limiar da probabilidade para considerar a imagem infectada (padrão: 0.5).",
    )
    return parser.parse_args()


def list_image_files(directory: str) -> List[str]:
    """Retorna uma lista de caminhos de arquivo para imagens com extensões válidas."""
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp"}
    files = []
    for fname in os.listdir(directory):
        ext = os.path.splitext(fname)[1].lower()
        if ext in valid_exts:
            files.append(os.path.join(directory, fname))
    return files


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir
    model_path = args.model_path
    threshold = args.threshold

    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Diretório de entrada '{input_dir}' não encontrado.")

    # Cria diretórios de saída
    healthy_dir = os.path.join(output_dir, "healthy")
    infected_dir = os.path.join(output_dir, "infected")
    os.makedirs(healthy_dir, exist_ok=True)
    os.makedirs(infected_dir, exist_ok=True)

    # Carrega o modelo treinado
    model = load_trained_model(model_path)

    files = list_image_files(input_dir)
    total = len(files)
    if total == 0:
        print("Nenhuma imagem encontrada para classificação.")
        return

    for i, fpath in enumerate(files, 1):
        try:
            image = Image.open(fpath).convert("RGB")
        except Exception as e:
            print(f"Erro ao abrir {fpath}: {e}")
            continue
        # Pré‑processa e prediz
        tensor = preprocess_image(image)
        prob = float(model.predict(tensor)[0][0])
        # Determina destino
        dest_dir = infected_dir if prob >= threshold else healthy_dir
        dest_path = os.path.join(dest_dir, os.path.basename(fpath))
        shutil.copy2(fpath, dest_path)
        print(f"[{i}/{total}] {os.path.basename(fpath)} → {'infected' if prob >= threshold else 'healthy'} (prob={prob:.2f})")

    print("Classificação concluída. Revise as pastas de saída para validar os resultados.")


if __name__ == "__main__":
    main()

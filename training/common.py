"""Constantes e utilitários compartilhados pelo treino, avaliação e exportação."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # raiz do repositório
TRAINING_DIR = ROOT / "training"
SERVER_DIR = ROOT / "backend"
DATASET_DIR = Path(os.environ.get("CASSAVA_DATASET_DIR", ROOT.parent / "cassava-leaf-disease-classification"))
CACHE_DIR = TRAINING_DIR / "data" / "cache"
SPLITS_CSV = TRAINING_DIR / "data" / "splits.csv"
MODELS_DIR = TRAINING_DIR / "models"
REPORTS_DIR = TRAINING_DIR / "reports"

# Ordem idêntica ao label_num_to_disease_map.json do Kaggle.
CLASS_CODES = ["CBB", "CBSD", "CGM", "CMD", "Healthy"]
CLASS_LABELS_PT = {
    "CBB": "Bacteriose (Xanthomonas phaseoli pv. manihotis)",
    "CBSD": "Estria marrom da mandioca (CBSD)",
    "CGM": "Mosqueado verde da mandioca (CGM)",
    "CMD": "Mosaico da mandioca (CMD)",
    "Healthy": "Folha sadia",
}
CBB_INDEX = CLASS_CODES.index("CBB")
HEALTHY_INDEX = CLASS_CODES.index("Healthy")

# Imagens do cache são salvas quadradas (a foto inteira é redimensionada, sem corte),
# igual ao que o servidor faz na inferência.
CACHE_SIZE = 288
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

"""Divide o dataset do Kaggle em treino/validação/teste e gera um cache redimensionado.

- Divisão estratificada 80/10/10 (semente fixa), gravada em data/splits.csv.
  O conjunto de teste nunca é usado no treino nem na escolha de limiares.
- Cada foto (800x600) vira um JPEG CACHE_SIZE x CACHE_SIZE em data/cache/,
  o que deixa a leitura no treino ~10x mais rápida.

Uso:
    python training/prepare_data.py
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split

from common import CACHE_DIR, CACHE_SIZE, CLASS_CODES, DATASET_DIR, SPLITS_CSV


def resize_one(args: tuple[Path, Path, int]) -> None:
    src, dst, size = args
    if dst.exists():
        return
    with Image.open(src) as im:
        im = im.convert("RGB").resize((size, size), Image.BILINEAR)
        im.save(dst, quality=95)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    df = pd.read_csv(DATASET_DIR / "train.csv")
    train_df, rest = train_test_split(df, test_size=0.2, stratify=df["label"], random_state=args.seed)
    val_df, test_df = train_test_split(rest, test_size=0.5, stratify=rest["label"], random_state=args.seed)
    train_df = train_df.assign(split="train")
    val_df = val_df.assign(split="val")
    test_df = test_df.assign(split="test")
    splits = pd.concat([train_df, val_df, test_df]).sort_values("image_id").reset_index(drop=True)
    SPLITS_CSV.parent.mkdir(parents=True, exist_ok=True)
    splits.to_csv(SPLITS_CSV, index=False)

    counts = splits.groupby(["split", "label"]).size().unstack(fill_value=0)
    counts.columns = [CLASS_CODES[c] for c in counts.columns]
    print(counts)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    jobs = [
        (DATASET_DIR / "train_images" / name, CACHE_DIR / name, CACHE_SIZE)
        for name in splits["image_id"]
    ]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for i, _ in enumerate(pool.map(resize_one, jobs, chunksize=64), 1):
            if i % 2000 == 0:
                print(f"{i}/{len(jobs)} imagens em cache")
    print(f"Cache pronto em {CACHE_DIR}")


if __name__ == "__main__":
    main()

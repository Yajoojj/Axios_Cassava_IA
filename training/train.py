"""Treina a EfficientNet-B0 (5 classes do Kaggle Cassava) com aprendizagem por transferência.

Por que 5 classes e não "infectado x sadio": as outras doenças (mosaico, estria marrom,
mosqueado verde) também deixam a folha amarelada/manchada. Ensinar o modelo a separá-las
é o que impede que um mosaico seja anunciado como bacteriose.

Uso:
    python training/train.py --epochs 10 --img-size 256
    python training/train.py --bench 20          # mede imagens/s e sai
    # ajuste fino em resolução maior a partir de um modelo já treinado (manchas pequenas ficam visíveis):
    python training/train.py --init training/models/greenleaf_effb0.pt --img-size 384 --cache-size 448 --epochs 4 --lr 3e-4 --batch-size 16 --out greenleaf_effb0_384
"""

from __future__ import annotations

import argparse
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
import timm
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader, Dataset
from torchvision.transforms import v2 as T

from common import (
    CACHE_SIZE,
    CBB_INDEX,
    CLASS_CODES,
    IMAGENET_MEAN,
    IMAGENET_STD,
    MODELS_DIR,
    REPORTS_DIR,
    SPLITS_CSV,
    cache_dir,
    write_json,
)

ARCH = "efficientnet_b0.ra_in1k"


class LeafDataset(Dataset):
    def __init__(self, df: pd.DataFrame, transform: T.Transform, cache_size: int = CACHE_SIZE):
        self.paths = [cache_dir(cache_size) / name for name in df["image_id"]]
        self.labels = df["label"].to_numpy()
        self.transform = transform

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, i: int):
        with Image.open(self.paths[i]) as im:
            x = self.transform(im.convert("RGB"))
        return x, int(self.labels[i])


def train_transform(size: int) -> T.Transform:
    return T.Compose([
        T.ToImage(),
        T.RandomResizedCrop(size, scale=(0.45, 1.0), ratio=(0.75, 1.333), antialias=True),
        T.RandomHorizontalFlip(),
        T.RandomVerticalFlip(),
        T.RandomApply([T.RandomRotation(25)], p=0.5),
        # Variações de luz de campo (sol forte, sombra, nublado).
        T.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.25, hue=0.03),
        T.ToDtype(torch.float32, scale=True),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        T.RandomErasing(p=0.2, scale=(0.02, 0.12)),
    ])


def eval_transform(size: int) -> T.Transform:
    return T.Compose([
        T.ToImage(),
        T.Resize((size, size), antialias=True),
        T.ToDtype(torch.float32, scale=True),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def pick_device(name: str) -> torch.device:
    if name in ("auto", "dml"):
        try:
            import torch_directml

            return torch_directml.device()
        except Exception as exc:  # noqa: BLE001
            if name == "dml":
                raise
            print(f"DirectML indisponível ({exc}); usando CPU.")
    return torch.device("cpu")


class SimpleAdamW(torch.optim.Optimizer):
    """AdamW só com mul_/add_/addcmul_/addcdiv_.

    O AdamW do PyTorch usa `lerp`, que o DirectML não implementa: cada passo copiava
    todos os pesos para a CPU e voltava, deixando a GPU AMD ociosa.
    """

    def __init__(self, params, lr=1e-3, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-2):
        super().__init__(params, dict(lr=lr, betas=betas, eps=eps, weight_decay=weight_decay))

    @torch.no_grad()
    def step(self):
        for group in self.param_groups:
            b1, b2 = group["betas"]
            for p in group["params"]:
                if p.grad is None:
                    continue
                state = self.state[p]
                if not state:
                    state["step"] = 0
                    state["m"] = torch.zeros_like(p)
                    state["v"] = torch.zeros_like(p)
                state["step"] += 1
                t = state["step"]
                m, v, g = state["m"], state["v"], p.grad
                m.mul_(b1).add_(g, alpha=1 - b1)
                v.mul_(b2).addcmul_(g, g, value=1 - b2)
                p.mul_(1 - group["lr"] * group["weight_decay"])
                denom = (v / (1 - b2**t)).sqrt_().add_(group["eps"])
                p.addcdiv_(m, denom, value=-group["lr"] / (1 - b1**t))


def class_weights(labels: np.ndarray) -> torch.Tensor:
    # Inverso da raiz da frequência: compensa o desbalanceamento (CMD = 61%, CBB = 5%)
    # sem distorcer demais as probabilidades.
    counts = np.bincount(labels, minlength=len(CLASS_CODES)).astype(np.float64)
    w = 1.0 / np.sqrt(counts)
    return torch.tensor(w / w.mean(), dtype=torch.float32)


@torch.no_grad()
def predict(model: nn.Module, loader: DataLoader, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    probs, labels = [], []
    for x, y in loader:
        logits = model(x.to(device))
        probs.append(torch.softmax(logits, dim=1).cpu().numpy())
        labels.append(y.numpy())
    return np.concatenate(probs), np.concatenate(labels)


def history_name(out: str) -> str:
    return "train_history.json" if out == "greenleaf_effb0" else f"train_history_{out}.json"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--img-size", type=int, default=256)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--val-batch-size", type=int, default=64, help="menor em resolução alta: a GPU de 8 GB não pode paginar")
    p.add_argument("--lr", type=float, default=6e-4)
    p.add_argument("--weight-decay", type=float, default=1e-2)
    p.add_argument("--label-smoothing", type=float, default=0.1)
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--device", default="auto", choices=["auto", "dml", "cpu"])
    p.add_argument("--bench", type=int, default=0, help="só mede velocidade por N passos")
    p.add_argument("--limit", type=int, default=0, help="usa só N imagens de treino (teste rápido)")
    p.add_argument("--out", default="greenleaf_effb0")
    p.add_argument("--cache-size", type=int, default=CACHE_SIZE, help="cache de prepare_data.py --cache-size")
    p.add_argument("--init", default="", help="checkpoint .pt para começar (ajuste fino em resolução maior)")
    p.add_argument("--warmup", type=float, default=0.5, help="aquecimento do LR, em épocas")
    args = p.parse_args()

    torch.manual_seed(42)
    np.random.seed(42)
    device = pick_device(args.device)
    print(f"Dispositivo: {device}")

    splits = pd.read_csv(SPLITS_CSV)
    train_df = splits[splits.split == "train"]
    val_df = splits[splits.split == "val"]
    if args.limit:
        train_df = train_df.sample(args.limit, random_state=0)
        val_df = val_df.sample(min(len(val_df), args.limit // 4), random_state=0)

    train_dl = DataLoader(
        LeafDataset(train_df, train_transform(args.img_size), args.cache_size),
        batch_size=args.batch_size, shuffle=True, drop_last=True,
        num_workers=args.workers, persistent_workers=args.workers > 0,
    )
    val_dl = DataLoader(
        LeafDataset(val_df, eval_transform(args.img_size), args.cache_size),
        batch_size=args.val_batch_size, num_workers=args.workers, persistent_workers=args.workers > 0,
    )

    arch = ARCH
    if args.init:
        init = torch.load(args.init, map_location="cpu", weights_only=False)
        arch = init["arch"]
    model = timm.create_model(arch, pretrained=not args.init, num_classes=len(CLASS_CODES), drop_rate=0.3, drop_path_rate=0.1)
    if args.init:
        model.load_state_dict(init["state_dict"])
        print(f"Começando de {args.init} (época {init['epoch']}, {init['img_size']} px)")
    model.to(device)
    criterion = nn.CrossEntropyLoss(
        weight=class_weights(train_df["label"].to_numpy()).to(device),
        label_smoothing=args.label_smoothing,
    )
    optimizer = SimpleAdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    steps_per_epoch = len(train_dl)
    total_steps = args.epochs * steps_per_epoch
    warmup = max(1, int(steps_per_epoch * args.warmup))

    def lr_at(step: int) -> float:
        if step < warmup:
            return (step + 1) / warmup
        progress = (step - warmup) / max(1, total_steps - warmup)
        return 0.02 + 0.98 * 0.5 * (1 + math.cos(math.pi * progress))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_at)

    if args.bench:
        model.train()
        it = iter(train_dl)
        for i in range(args.bench + 2):
            if i == 2:
                t0 = time.perf_counter()
            x, y = next(it)
            loss = criterion(model(x.to(device)), y.to(device))
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            _ = loss.item()
        dt = time.perf_counter() - t0
        ips = args.bench * args.batch_size / dt
        print(f"{ips:.1f} imagens/s -> ~{len(train_df) / ips / 60:.1f} min por época")
        return

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    ckpt_path = MODELS_DIR / f"{args.out}.pt"
    history = []
    best_f1 = -1.0
    step = 0
    for epoch in range(1, args.epochs + 1):
        model.train()
        t0 = time.perf_counter()
        running, seen = 0.0, 0
        for x, y in train_dl:
            x, y = x.to(device), y.to(device)
            loss = criterion(model(x), y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            scheduler.step()
            step += 1
            running += loss.item() * len(y)
            seen += len(y)
            if step % 100 == 0:
                print(f"  época {epoch} passo {step % steps_per_epoch or steps_per_epoch}/{steps_per_epoch} "
                      f"loss {running / seen:.4f} ({seen / (time.perf_counter() - t0):.1f} img/s)", flush=True)

        probs, labels = predict(model, val_dl, device)
        preds = probs.argmax(1)
        acc = float((preds == labels).mean())
        f1_macro = float(f1_score(labels, preds, average="macro"))
        cbb_true = labels == CBB_INDEX
        cbb_recall = float((preds[cbb_true] == CBB_INDEX).mean())
        row = {
            "epoch": epoch,
            "train_loss": running / seen,
            "val_accuracy": acc,
            "val_f1_macro": f1_macro,
            "val_cbb_recall": cbb_recall,
            "minutes": (time.perf_counter() - t0) / 60,
        }
        history.append(row)
        print(f"época {epoch}: loss {row['train_loss']:.4f} | val acc {acc:.4f} | F1 macro {f1_macro:.4f} "
              f"| recall CBB {cbb_recall:.3f} | {row['minutes']:.1f} min", flush=True)

        if f1_macro > best_f1:
            best_f1 = f1_macro
            torch.save({
                "arch": arch,
                "img_size": args.img_size,
                "cache_size": args.cache_size,
                "classes": CLASS_CODES,
                "state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
                "epoch": epoch,
                "val_f1_macro": f1_macro,
                "val_accuracy": acc,
            }, ckpt_path)
            print(f"  -> melhor modelo salvo em {ckpt_path}")
        write_json(REPORTS_DIR / history_name(args.out), {"args": vars(args), "history": history})


if __name__ == "__main__":
    main()

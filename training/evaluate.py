"""Calibra a regra de decisão na validação e mede tudo no conjunto de teste.

Roda o MESMO código do servidor (backend/app: ONNX + análise de cor) sobre as fotos
originais do Kaggle, então os números valem para o que o app vai receber.

1. Validação: escolhe o peso da rede (MODEL_WEIGHT) e o limiar (CONFIDENCE_THRESHOLD)
   que maximizam o F-beta da bacteriose. beta=1 (padrão) equilibra alarmes falsos e
   bacterioses perdidas; beta=2 dá mais peso a não deixar passar folha doente.
2. Teste: métricas finais (5 classes e bacteriose sim/não), matriz de confusão,
   comparação com a regra antiga só por cor e tempo de inferência.

Uso:
    python training/evaluate.py
    python training/evaluate.py --name greenleaf_effb0_384 --beta 1
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import date

import matplotlib
import numpy as np
import pandas as pd
import torch
from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    fbeta_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from common import CACHE_SIZE, CBB_INDEX, CLASS_CODES, DATASET_DIR, MODELS_DIR, REPORTS_DIR, SERVER_DIR, SPLITS_CSV, read_json, write_json

sys.path.insert(0, str(SERVER_DIR))
from app.analysis import DecisionSettings, analyze, resize_max_side  # noqa: E402
from app.hsv import lesion_ratio  # noqa: E402
from app.model import Predictor  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SERVER_MODELS = SERVER_DIR / "models"
ANALYSIS_MAX_SIDE = 768


def run_split(predictor: Predictor, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    # Limiar 0: tudo "Infectado", para a taxa de manchas não ser zerada antes da calibração
    # (o servidor zera a taxa quando não é bacteriose, depois de decidir).
    settings = DecisionSettings(threshold=0.0, model_weight=1.0)
    probs, ratios, raw_ratios, times = [], [], [], []
    for i, name in enumerate(df["image_id"], 1):
        # PIL em vez de cv2.imread: o OpenCV não abre caminhos com acento no Windows.
        with Image.open(DATASET_DIR / "train_images" / name) as im:
            rgb = resize_max_side(np.asarray(im.convert("RGB")), ANALYSIS_MAX_SIDE)
        t0 = time.perf_counter()
        out = analyze(rgb, predictor, settings, with_overlay=False)
        times.append(time.perf_counter() - t0)
        probs.append([out["class_probabilities"][c] for c in CLASS_CODES])
        ratios.append(out["ratio"])
        raw_ratios.append(lesion_ratio(rgb)[0])  # só cor, sem a rede
        if i % 500 == 0:
            print(f"  {i}/{len(df)}", flush=True)
    return np.array(probs), np.array(ratios), np.array(raw_ratios), float(np.mean(times) * 1000)


def combined(probs: np.ndarray, ratios: np.ndarray, w: float) -> np.ndarray:
    return w * probs[:, CBB_INDEX] + (1 - w) * np.minimum(ratios / 0.20, 1.0)


def binary_metrics(y_true: np.ndarray, y_pred: np.ndarray, score: np.ndarray | None = None) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    m = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred),
        "specificity": tn / (tn + fp),
        "f1": f1_score(y_true, y_pred),
        "confusion": {"tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn)},
    }
    if score is not None:
        m["roc_auc"] = roc_auc_score(y_true, score)
    return {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in m.items()}


def plot_confusion(cm: np.ndarray, path) -> None:
    norm = cm / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    ax.imshow(norm, cmap="Greens", vmin=0, vmax=1)
    ax.set_xticks(range(len(CLASS_CODES)), CLASS_CODES)
    ax.set_yticks(range(len(CLASS_CODES)), CLASS_CODES)
    ax.set_xlabel("Previsto")
    ax.set_ylabel("Real")
    ax.set_title("Matriz de confusão — conjunto de teste")
    for i in range(len(CLASS_CODES)):
        for j in range(len(CLASS_CODES)):
            ax.text(j, i, f"{cm[i, j]}\n{norm[i, j]:.0%}", ha="center", va="center",
                    color="white" if norm[i, j] > 0.5 else "#222", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


NAMES_PT = {"CBB": "Bacteriose (CBB)", "CBSD": "Estria marrom (CBSD)", "CGM": "Mosqueado verde (CGM)",
            "CMD": "Mosaico (CMD)", "Healthy": "Sadia"}


def write_markdown(m: dict, path) -> None:
    pct = lambda v: f"{v * 100:.1f}%"  # noqa: E731
    mc, b = m["multiclass"], m["bacteriose"]
    new, old = b["greenleaf_v2"], b["hsv_only_rule"]
    lines = [
        "# Resultados — GreenLeaf IA",
        "",
        f"Modelo `{m['model']}`, conjunto de **teste** com {m['test_images']} fotos do Kaggle nunca usadas no treino "
        "nem na calibração (divisão estratificada 80/10/10, semente 42). Medido com o mesmo código do servidor.",
        "",
        "## Classificação das 5 classes",
        "",
        "| Classe | Precisão | Revocação | F1 | Fotos |",
        "|---|---|---|---|---|",
    ]
    for c in CLASS_CODES:
        r = mc["per_class"][c]
        lines.append(f"| {NAMES_PT[c]} | {pct(r['precision'])} | {pct(r['recall'])} | {pct(r['f1-score'])} | {int(r['support'])} |")
    lines += [
        f"| **Acurácia global** | | | **{pct(mc['accuracy'])}** | |",
        f"| **F1 macro** | | | **{pct(mc['f1_macro'])}** | |",
        "",
        "![Matriz de confusão](confusion_matrix.png)",
        "",
        "## Bacteriose sim/não (o que o app mostra)",
        "",
        f"Regra: `probabilidade = {b['decision']['model_weight']} × P(CBB) + {1 - b['decision']['model_weight']:.2f} × prob. pela cor`, "
        f"bacteriose se ≥ **{b['decision']['threshold']}** (escolhido por {b['decision']['objective']}).",
        "",
        "| Métrica | GreenLeaf (rede + cor) | Só cor, sem rede |",
        "|---|---|---|",
    ]
    for key, label in (("recall", "Revocação (bacterioses encontradas)"), ("precision", "Precisão (alarmes corretos)"),
                       ("specificity", "Especificidade (não-bacterioses descartadas)"), ("f1", "F1"),
                       ("accuracy", "Acurácia"), ("roc_auc", "AUC ROC")):
        lines.append(f"| {label} | {pct(new[key])} | {pct(old[key])} |")
    cn, co = new["confusion"], old["confusion"]
    lines += [
        f"| Verdadeiros positivos / falsos negativos | {cn['tp']} / {cn['fn']} | {co['tp']} / {co['fn']} |",
        f"| Falsos positivos / verdadeiros negativos | {cn['fp']} / {cn['tn']} | {co['fp']} / {co['tn']} |",
        "",
        f"Tempo médio por foto em CPU (rede + cor, sem rede de celular): **{m['latency_ms_per_image_cpu']:.0f} ms**.",
        "",
        "A severidade (Leve/Moderada/Grave) vem da taxa de manchas medida pela cor; o dataset não tem rótulo de severidade,",
        "então ela não entra nestas métricas.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--name", default="greenleaf_effb0")
    p.add_argument("--beta", type=float, default=1.0)
    p.add_argument("--no-tta", action="store_true")
    p.add_argument("--limit", type=int, default=0, help="usa só N imagens por conjunto (teste rápido)")
    args = p.parse_args()

    ckpt = torch.load(MODELS_DIR / f"{args.name}.pt", map_location="cpu", weights_only=False)
    meta_path = SERVER_MODELS / f"{args.name}.json"
    meta = {
        "version": f"{args.name}-{date.today().isoformat()}",
        "arch": ckpt["arch"],
        "img_size": ckpt["img_size"],
        "cache_size": int(ckpt.get("cache_size", CACHE_SIZE)),
        "classes": CLASS_CODES,
        "input": "float32 [N,3,S,S] RGB 0-1; normalização ImageNet dentro do grafo",
        "outputs": {"probs": "softmax [N,5]", "cam": "mapa de ativação [N,5,S/32,S/32]"},
        "tta_hflip": not args.no_tta,
        "decision": {"threshold": 0.5, "model_weight": 1.0},
    }
    write_json(meta_path, meta)
    predictor = Predictor(SERVER_MODELS / f"{args.name}.onnx", meta_path, tta=not args.no_tta, threads=4)

    splits = pd.read_csv(SPLITS_CSV)
    val_df, test_df = splits[splits.split == "val"], splits[splits.split == "test"]
    if args.limit:
        val_df = val_df.groupby("label").head(args.limit // len(CLASS_CODES))
        test_df = test_df.groupby("label").head(args.limit // len(CLASS_CODES))

    print("Validação (calibração)...")
    val_probs, val_ratios, _, _ = run_split(predictor, val_df)
    y_val = (val_df["label"].to_numpy() == CBB_INDEX).astype(int)
    per_weight = {}
    for w in np.round(np.arange(0.5, 1.0001, 0.05), 2):
        score = combined(val_probs, val_ratios, w)
        per_weight[float(w)] = max(
            (fbeta_score(y_val, (score >= t).astype(int), beta=args.beta), float(t))
            for t in np.round(np.arange(0.05, 0.951, 0.01), 2)
        )
    # A cor só entra se melhorar o F-beta da validação em mais de 0,01: com ~100 bacterioses na
    # validação, diferenças menores são ruído (a taxa de manchas sozinha tem AUC ~0,4–0,5).
    best_w = max(per_weight, key=lambda w: per_weight[w][0])
    w_best = best_w if per_weight[best_w][0] > per_weight[1.0][0] + 0.01 else 1.0
    best = (per_weight[w_best][0], w_best, per_weight[w_best][1])
    _, w_best, t_best = best
    print(f"  peso da rede = {w_best}, limiar = {t_best} (F{args.beta:g} val = {best[0]:.4f})")

    print("Teste...")
    test_probs, test_ratios, test_raw_ratios, ms = run_split(predictor, test_df)
    y5 = test_df["label"].to_numpy()
    pred5 = test_probs.argmax(1)
    cm = confusion_matrix(y5, pred5, labels=list(range(len(CLASS_CODES))))
    report5 = classification_report(y5, pred5, target_names=CLASS_CODES, output_dict=True, zero_division=0)

    y_bin = (y5 == CBB_INDEX).astype(int)
    score = combined(test_probs, test_ratios, w_best)
    new_rule = binary_metrics(y_bin, (score >= t_best).astype(int), score)
    # Regra só por cor (o que o servidor faz sem modelo): taxa >= 2% ou prob. HSV >= 0,45.
    hsv_prob = np.minimum(test_raw_ratios / 0.20, 1.0)
    old_rule = binary_metrics(y_bin, ((test_raw_ratios >= 0.02) | (hsv_prob >= 0.45)).astype(int), hsv_prob)
    np.savez_compressed(
        REPORTS_DIR / f"predictions_{args.name}.npz",
        val_ids=val_df["image_id"].to_numpy(), val_labels=val_df["label"].to_numpy(), val_probs=val_probs, val_ratios=val_ratios,
        test_ids=test_df["image_id"].to_numpy(), test_labels=y5, test_probs=test_probs, test_ratios=test_ratios,
    )

    history = REPORTS_DIR / ("train_history.json" if args.name == "greenleaf_effb0" else f"train_history_{args.name}.json")
    metrics = {
        "model": meta["version"],
        "test_images": int(len(test_df)),
        "multiclass": {
            "accuracy": float(report5["accuracy"]),
            "f1_macro": float(report5["macro avg"]["f1-score"]),
            "per_class": {c: {k: float(report5[c][k]) for k in ("precision", "recall", "f1-score", "support")} for c in CLASS_CODES},
            "confusion_matrix": cm.tolist(),
        },
        "bacteriose": {
            "decision": {"model_weight": w_best, "threshold": t_best, "objective": f"F{args.beta:g} na validação"},
            "greenleaf_v2": new_rule,
            "hsv_only_rule": old_rule,
        },
        "latency_ms_per_image_cpu": ms,
        "training": read_json(history) if history.exists() else None,
    }
    write_json(REPORTS_DIR / "metrics.json", metrics)
    plot_confusion(cm, REPORTS_DIR / "confusion_matrix.png")
    write_markdown(metrics, REPORTS_DIR / "metrics.md")

    meta["decision"] = {"threshold": t_best, "model_weight": w_best}
    meta["metrics_test"] = {
        "accuracy_5_classes": metrics["multiclass"]["accuracy"],
        "f1_macro_5_classes": metrics["multiclass"]["f1_macro"],
        "bacteriose_recall": new_rule["recall"],
        "bacteriose_precision": new_rule["precision"],
        "bacteriose_roc_auc": new_rule["roc_auc"],
    }
    write_json(meta_path, meta)

    pc = metrics["multiclass"]["per_class"]
    print(f"\n5 classes: acurácia {metrics['multiclass']['accuracy']:.4f} | F1 macro {metrics['multiclass']['f1_macro']:.4f}")
    for c in CLASS_CODES:
        print(f"  {c:8s} P {pc[c]['precision']:.3f}  R {pc[c]['recall']:.3f}  F1 {pc[c]['f1-score']:.3f}  n={int(pc[c]['support'])}")
    for name, m in (("GreenLeaf", new_rule), ("Só cor", old_rule)):
        print(f"Bacteriose — {name}: P {m['precision']:.3f} R {m['recall']:.3f} F1 {m['f1']:.3f} "
              f"espec. {m['specificity']:.3f} AUC {m['roc_auc']:.3f}")
    print(f"Tempo médio (CPU, modelo + cor): {ms:.0f} ms/imagem")


if __name__ == "__main__":
    main()

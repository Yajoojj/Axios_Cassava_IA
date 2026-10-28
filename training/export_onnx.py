"""Exporta o melhor checkpoint para ONNX, com normalização e mapa de atenção (CAM) dentro do grafo.

Entrada:  float32 [N, 3, S, S], valores 0–1 (RGB).
Saídas:   probs [N, 5] (softmax) e cam [N, 5, S/32, S/32] (mapa de ativação de cada classe).

O CAM sai de graça porque a cabeça da EfficientNet é "média global + camada linear":
o mapa de uma classe é a soma dos mapas de características ponderada pelos pesos dessa classe.

Uso:
    python training/export_onnx.py
"""

from __future__ import annotations

import argparse

import numpy as np
import onnxruntime as ort
import timm
import torch
import torch.nn as nn

from common import IMAGENET_MEAN, IMAGENET_STD, MODELS_DIR, SERVER_DIR

SERVER_MODELS = SERVER_DIR / "models"


class ExportWrapper(nn.Module):
    def __init__(self, model: nn.Module):
        super().__init__()
        self.model = model
        self.register_buffer("mean", torch.tensor(IMAGENET_MEAN).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor(IMAGENET_STD).view(1, 3, 1, 1))

    def forward(self, x: torch.Tensor):
        x = (x - self.mean) / self.std
        features = self.model.forward_features(x)
        logits = self.model.forward_head(features)
        w = self.model.get_classifier().weight  # [classes, canais]
        cam = torch.einsum("nchw,kc->nkhw", features, w)
        return torch.softmax(logits, dim=1), cam


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", default=str(MODELS_DIR / "greenleaf_effb0.pt"))
    p.add_argument("--name", default="greenleaf_effb0")
    args = p.parse_args()

    ckpt = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model = timm.create_model(ckpt["arch"], pretrained=False, num_classes=len(ckpt["classes"]))
    model.load_state_dict(ckpt["state_dict"])
    wrapper = ExportWrapper(model).eval()

    size = ckpt["img_size"]
    dummy = torch.rand(2, 3, size, size)
    SERVER_MODELS.mkdir(parents=True, exist_ok=True)
    out_path = SERVER_MODELS / f"{args.name}.onnx"
    tmp_path = MODELS_DIR / "export_tmp.onnx"
    torch.onnx.export(
        wrapper, dummy, str(tmp_path),
        input_names=["image"], output_names=["probs", "cam"],
        dynamic_axes={"image": {0: "batch"}, "probs": {0: "batch"}, "cam": {0: "batch"}},
        opset_version=17,
    )
    out_path.write_bytes(tmp_path.read_bytes())
    tmp_path.unlink()

    with torch.no_grad():
        ref_probs, ref_cam = wrapper(dummy)
    sess = ort.InferenceSession(out_path.read_bytes(), providers=["CPUExecutionProvider"])
    probs, cam = sess.run(None, {"image": dummy.numpy()})
    print(f"ONNX salvo em {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")
    print(f"diferença máx. probs: {np.abs(probs - ref_probs.numpy()).max():.2e} | cam: {np.abs(cam - ref_cam.numpy()).max():.2e}")


if __name__ == "__main__":
    main()

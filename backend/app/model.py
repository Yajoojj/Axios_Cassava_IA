"""Carrega o modelo ONNX e roda a inferência (probabilidades das 5 classes + mapa de atenção)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class ModelOutput:
    probabilities: np.ndarray  # (5,) somando 1, na ordem de `classes`
    attention: np.ndarray  # (5, h, w) mapa de ativação de cada classe (CAM)


class Predictor:
    """Envolve a sessão do ONNX Runtime. A normalização ImageNet já está dentro do grafo."""

    def __init__(self, model_path: Path, meta_path: Path, tta: bool = True, threads: int = 2):
        import onnxruntime as ort

        self.meta = json.loads(meta_path.read_text(encoding="utf-8"))
        self.classes: list[str] = self.meta["classes"]
        self.img_size: int = int(self.meta["img_size"])
        self.tta = tta
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads  # 2 no servidor: o plano gratuito da Render tem CPU compartilhada
        # Sem espera ativa: em CPU compartilhada, threads "girando" roubam tempo de quem está trabalhando.
        options.add_session_config_entry("session.intra_op.allow_spinning", "0")
        # Ler os bytes contorna caminhos com acento no Windows ("Programação").
        self.session = ort.InferenceSession(model_path.read_bytes(), options, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

    @property
    def version(self) -> str:
        return str(self.meta.get("version", "desconhecida"))

    def preprocess(self, rgb: np.ndarray) -> np.ndarray:
        # Foto inteira redimensionada para quadrado, sem corte, pelo MESMO caminho do treino
        # (PIL bilinear até o tamanho do cache e depois até a entrada da rede). Trocar por
        # cv2.INTER_AREA direto custava ~3 pontos de acurácia no teste.
        from PIL import Image

        im = Image.fromarray(rgb)
        cache = int(self.meta.get("cache_size", 0))
        if cache:
            im = im.resize((cache, cache), Image.BILINEAR)
        im = im.resize((self.img_size, self.img_size), Image.BILINEAR)
        x = np.asarray(im, dtype=np.float32) / 255.0
        return np.transpose(x, (2, 0, 1))[None]

    def predict(self, rgb: np.ndarray) -> ModelOutput:
        x = self.preprocess(rgb)
        if self.tta:
            x = np.concatenate([x, x[:, :, :, ::-1]], axis=0)
        probs, cam = self.session.run(None, {self.input_name: np.ascontiguousarray(x)})
        if self.tta:
            probs = probs.mean(axis=0, keepdims=True)
            cam = (cam[0:1] + cam[1:2, :, :, ::-1]) / 2
        return ModelOutput(probabilities=probs[0], attention=cam[0])


def upsample_attention(cam: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Mapa de atenção normalizado (0–1 do pico) no tamanho da imagem. O `cam` tem só S/32 de lado (8x8).

    As 4 células dos cantos são zeradas: no teste, 41% dos picos caíam nelas (efeito do preenchimento
    de borda das convoluções), o que desenhava arcos amarelos nos cantos de quase toda foto.
    """
    cam = np.maximum(cam, 0)
    if min(cam.shape) > 2:
        cam = cam.copy()
        cam[[0, 0, -1, -1], [0, -1, 0, -1]] = 0
    peak = float(cam.max())
    if peak <= 0:
        return np.zeros(shape, dtype=np.float32)
    return cv2.resize((cam / peak).astype(np.float32), (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)


def attention_mask(cam: np.ndarray, shape: tuple[int, int], threshold: float = 0.55) -> np.ndarray:
    """Região contínua em torno do pico onde a ativação passa de `threshold` do máximo, no tamanho da imagem.

    Só o trecho que contém o pico: os outros costumam ser arcos nos cantos da foto, efeito da borda
    nas convoluções, e não lesão.
    """
    up = upsample_attention(cam, shape)
    mask = up >= threshold
    if not mask.any():
        return mask
    _, labels = cv2.connectedComponents(mask.astype("uint8"), connectivity=8)
    peak = np.unravel_index(int(np.argmax(up)), up.shape)
    return labels == labels[peak]

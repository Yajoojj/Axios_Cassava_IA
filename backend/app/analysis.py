"""Regra de decisão: junta a rede neural e a análise de cor numa resposta para o app.

Função pura (sem FastAPI), para poder ser testada e reutilizada na avaliação.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .hsv import around, classify_severity, convex_region, create_overlay, encode_jpeg_data_url, lesion_ratio, main_leaf_region
from .model import Predictor, attention_mask

LABELS_PT = {
    "CBB": "Bacteriose",
    "CBSD": "Estria marrom (CBSD)",
    "CGM": "Mosqueado verde (CGM)",
    "CMD": "Mosaico (CMD)",
    "Healthy": "Sadia",
}


# Fração da região de decisão da rede que a folha escolhida precisa cobrir para servir de recorte.
MIN_LEAF_COVERAGE = 0.5


@dataclass(frozen=True)
class DecisionSettings:
    threshold: float  # probabilidade combinada a partir da qual a folha é "Infectado"
    model_weight: float  # peso da rede na combinação com a cor (0–1)
    hsv_only_threshold: float = 0.45  # usado só quando o modelo não carregou
    min_infection_ratio: float = 0.02  # idem


class ImageQualityError(ValueError):
    """Foto que não dá para analisar (pequena demais, escura ou estourada)."""


def resize_max_side(rgb: np.ndarray, max_side: int) -> np.ndarray:
    h, w = rgb.shape[:2]
    scale = max_side / max(h, w)
    if scale >= 1:
        return rgb
    return cv2.resize(rgb, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)


def check_quality(rgb: np.ndarray, min_side: int = 160) -> None:
    if min(rgb.shape[:2]) < min_side:
        raise ImageQualityError("Foto pequena demais. Aproxime a câmera da folha.")
    brightness = float(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).mean())
    if brightness < 25:
        raise ImageQualityError("Foto escura demais. Fotografe com mais luz.")
    if brightness > 240:
        raise ImageQualityError("Foto clara demais (luz estourada). Evite o sol direto na lente.")


def _focus_region(cam: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Região ampla em torno de onde a rede olhou; fora dela, cor amarelada/escura não conta como mancha."""
    region = attention_mask(cam, shape, threshold=0.3)
    k = max(3, round(max(shape) * 0.04)) | 1
    return cv2.dilate(region.astype("uint8"), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) > 0


def analyze(rgb: np.ndarray, predictor: Predictor | None, settings: DecisionSettings, with_overlay: bool = True) -> dict:
    ratio, leaf, lesions = lesion_ratio(rgb)
    attention = None
    extras: dict = {}

    if predictor is not None:
        out = predictor.predict(rgb)
        classes = predictor.classes
        probs = out.probabilities
        cbb = classes.index("CBB")
        top = int(np.argmax(probs))
        model_probability = float(probs[cbb])

        if classes[top] == "Healthy":
            # Folha sadia para a rede: bordas, sombras e solo não viram "manchas".
            lesions = np.zeros_like(lesions)
            cam = np.maximum(out.attention[top], 0)
        else:
            # Mapa de "doença": atenção de cada classe doente ponderada pela sua probabilidade.
            # A análise de cor sozinha marca bordas, sombras e solo; contamos só o que está perto
            # da região que a rede usou para decidir.
            sick = [i for i, c in enumerate(classes) if c != "Healthy"]
            cam = np.tensordot(probs[sick], np.maximum(out.attention[sick], 0), axes=1)
            lesions &= _focus_region(cam, rgb.shape[:2])
        # Só a folha analisada conta: com mato ao fundo, todo verde da cena passaria por "folha"
        # e a folhagem seca entre as folhas, por "mancha" (issue #7). Folha amarelada, seca ou
        # murcha quase não tem verde e a "folha" achada pela cor seria o mato; nesse caso, sem recorte.
        decision_region = attention_mask(cam, rgb.shape[:2])
        region = main_leaf_region(leaf, decision_region)
        covered = float((decision_region & region).sum()) / max(float(decision_region.sum()), 1.0)
        clip = None
        if covered >= MIN_LEAF_COVERAGE:
            leaf &= region
            lesions &= around(region, 0.03)
            clip = convex_region(region)
        if classes[top] != "Healthy":
            # O mapa de atenção é 8x8 ampliado: sem o recorte, o contorno invade o fundo.
            attention = decision_region if clip is None else decision_region & clip
        leaf_area = float((leaf | lesions).sum())
        ratio = float(lesions.sum()) / leaf_area if leaf_area > 0 else 0.0
        hsv_probability = min(ratio / 0.20, 1.0)
        probability = settings.model_weight * model_probability + (1 - settings.model_weight) * hsv_probability
        infected = probability >= settings.threshold
        if not infected:
            # Sem bacteriose, nada de "mancha suspeita" em vermelho: a cor sozinha não distingue
            # bacteriose de mosaico, sombra ou folha velha (AUC 0,45–0,62 na validação).
            lesions = np.zeros_like(lesions)
            ratio = 0.0

        top_code = classes[top]
        extras = {
            "diagnosis": {"code": top_code, "label": LABELS_PT.get(top_code, top_code), "probability": float(probs[top])},
            "class_probabilities": {c: float(p) for c, p in zip(classes, probs)},
            # Outra doença provável quando a bacteriose foi descartada — o app pode avisar o produtor.
            "other_disease": top_code if (not infected and top_code not in ("CBB", "Healthy")) else None,
            "model_version": predictor.version,
        }
    else:
        model_probability = None
        hsv_probability = min(ratio / 0.20, 1.0)
        probability = hsv_probability
        infected = ratio >= settings.min_infection_ratio or probability >= settings.hsv_only_threshold
        extras = {"diagnosis": None, "class_probabilities": None, "other_disease": None, "model_version": None}

    result = {
        "probability": float(min(max(probability, 0.0), 1.0)),
        "model_probability": model_probability,
        "hsv_probability": float(hsv_probability),
        "class": "Infectado" if infected else "Saudavel",
        "ratio": float(min(max(ratio, 0.0), 1.0)),
        "severity": classify_severity(ratio),
        **extras,
    }
    if with_overlay:
        result["overlay"] = encode_jpeg_data_url(create_overlay(rgb, leaf, lesions, attention))
    return result

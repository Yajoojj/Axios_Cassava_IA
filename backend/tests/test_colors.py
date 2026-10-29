"""Cor: amarelo é folha (não mancha); só necrose conta; sem bacteriose, nada em vermelho."""

from __future__ import annotations

import numpy as np

from app.analysis import DecisionSettings, analyze
from app.hsv import lesion_ratio
from app.model import ModelOutput

SOIL = (110, 85, 60)


def scene(leaf_rgb, size=(480, 640)):
    h, w = size
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = SOIL
    yy, xx = np.mgrid[0:h, 0:w]
    leaf = ((xx - w / 2) / (w * 0.3)) ** 2 + ((yy - h / 2) / (h * 0.35)) ** 2 <= 1
    img[leaf] = leaf_rgb
    return img, leaf, (yy, xx)


def test_yellow_leaf_is_leaf_not_lesion():
    img, leaf, _ = scene((220, 200, 50))  # folha amarelada (clorose / mosaico)
    ratio, leaf_mask, lesions = lesion_ratio(img)
    assert ratio < 0.01
    assert leaf_mask[leaf].mean() > 0.9


def test_brown_spot_on_leaf_is_lesion():
    img, leaf, (yy, xx) = scene((70, 150, 55))
    spot = (xx - 320) ** 2 + (yy - 240) ** 2 <= 30**2
    img[spot] = (130, 80, 35)  # necrose marrom
    ratio, _, lesions = lesion_ratio(img)
    assert lesions[spot].mean() > 0.8
    assert 0.02 < ratio < 0.2


def test_dark_shadow_beside_leaf_is_not_lesion():
    img, leaf, (yy, xx) = scene((70, 150, 55))
    shadow = (xx > 520) & (xx < 600) & (yy > 100) & (yy < 380) & ~leaf
    img[shadow] = (40, 32, 25)
    _, _, lesions = lesion_ratio(img)
    assert not lesions[shadow].any()


class StubPredictor:
    classes = ["CBB", "CBSD", "CGM", "CMD", "Healthy"]
    version = "stub"

    def __init__(self, probs):
        self.probs = np.array(probs, dtype=np.float32)

    def predict(self, rgb):
        cam = np.zeros((5, 8, 8), dtype=np.float32)
        cam[:, 3:5, 3:5] = 1.0
        return ModelOutput(probabilities=self.probs, attention=cam)


def test_no_red_spots_without_bacteriose():
    img, _, (yy, xx) = scene((70, 150, 55))
    img[(xx - 320) ** 2 + (yy - 240) ** 2 <= 30**2] = (130, 80, 35)
    settings = DecisionSettings(threshold=0.5, model_weight=1.0)
    mosaic = analyze(img, StubPredictor([0.05, 0.05, 0.05, 0.8, 0.05]), settings, with_overlay=False)
    assert mosaic["class"] == "Saudavel" and mosaic["other_disease"] == "CMD"
    assert mosaic["ratio"] == 0.0
    bacteriose = analyze(img, StubPredictor([0.8, 0.05, 0.05, 0.05, 0.05]), settings, with_overlay=False)
    assert bacteriose["class"] == "Infectado" and bacteriose["ratio"] > 0.02

"""Testes do contrato da API — os mesmos campos e tipos que o app valida em src/domain/schemas.ts."""

from __future__ import annotations

import io
import re

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import config, main

client = TestClient(main.app)
IMAGE_DATA_URL = re.compile(r"^data:image/(png|jpeg);base64,[A-Za-z0-9+/]+=*$")


def leaf_photo(size=(640, 480), spots=True, fmt="JPEG") -> bytes:
    """Folha verde sintética sobre fundo de solo, com manchas marrons opcionais."""
    w, h = size
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = (110, 85, 60)
    yy, xx = np.mgrid[0:h, 0:w]
    leaf = ((xx - w / 2) / (w * 0.38)) ** 2 + ((yy - h / 2) / (h * 0.4)) ** 2 <= 1
    img[leaf] = (70, 150, 55)
    if spots:
        for cx, cy in ((w * 0.4, h * 0.45), (w * 0.6, h * 0.55), (w * 0.5, h * 0.35)):
            spot = (xx - cx) ** 2 + (yy - cy) ** 2 <= (w * 0.04) ** 2
            img[spot & leaf] = (120, 75, 30)
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format=fmt)
    return buf.getvalue()


def post(data: bytes, content_type="image/jpeg", name="folha.jpg"):
    return client.post("/predict", files={"image": (name, data, content_type)})


def test_health_contract():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    for key, typ in (("version", str), ("environment", str), ("model_loaded", bool), ("supabase_logging", bool)):
        assert isinstance(body[key], typ)


@pytest.mark.parametrize("fmt,ctype", [("JPEG", "image/jpeg"), ("PNG", "image/png")])
def test_predict_contract(fmt, ctype):
    res = post(leaf_photo(fmt=fmt), ctype, f"folha.{fmt.lower()}")
    assert res.status_code == 200, res.text
    body = res.json()
    for key in ("probability", "hsv_probability", "ratio"):
        assert 0.0 <= body[key] <= 1.0
    assert body["model_probability"] is None or 0.0 <= body["model_probability"] <= 1.0
    assert body["class"] in ("Infectado", "Saudavel")
    assert body["severity"] in ("Leve", "Moderada", "Grave")
    assert body["processing_time_ms"] >= 0
    assert IMAGE_DATA_URL.match(body["overlay"])


def test_model_extras_are_consistent():
    if main.predictor is None:
        pytest.skip("modelo não encontrado")
    body = post(leaf_photo()).json()
    probs = body["class_probabilities"]
    assert set(probs) == {"CBB", "CBSD", "CGM", "CMD", "Healthy"}
    assert abs(sum(probs.values()) - 1) < 1e-3
    assert body["model_probability"] == pytest.approx(probs["CBB"])
    assert body["diagnosis"]["code"] == max(probs, key=probs.get)
    if body["class"] == "Infectado":
        assert body["other_disease"] is None


def test_rejects_wrong_format():
    assert post(b"GIF89a....", "image/gif", "x.gif").status_code == 400
    # Tipo declarado como JPEG mas conteúdo não é imagem.
    assert post(b"nao sou uma imagem", "image/jpeg").status_code == 400


def test_rejects_too_large(monkeypatch):
    monkeypatch.setattr(config, "MAX_UPLOAD_BYTES", 1000)
    assert post(leaf_photo()).status_code == 413


def test_rejects_low_quality():
    assert post(leaf_photo(size=(120, 90))).status_code == 422
    dark = io.BytesIO()
    Image.new("RGB", (640, 480), (5, 5, 5)).save(dark, format="JPEG")
    assert post(dark.getvalue()).status_code == 422


def test_metrics_counts_predictions():
    before = client.get("/metrics").json()["total_predictions"]
    post(leaf_photo())
    assert client.get("/metrics").json()["total_predictions"] == before + 1

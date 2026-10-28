"""GreenLeaf IA — servidor de inferência (FastAPI + ONNX Runtime).

Substitui o backend do Axios Cassava IA mantendo o mesmo contrato:
`POST /predict`, `GET /health`, `GET /metrics`. Os campos novos da resposta
(`diagnosis`, `class_probabilities`, `other_disease`, `model_version`) são extras;
o app atual os ignora sem quebrar.
"""

from __future__ import annotations

import logging
import time
from io import BytesIO

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps

from . import config
from .analysis import DecisionSettings, ImageQualityError, analyze, check_quality, resize_max_side
from .model import Predictor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("greenleaf")

VERSION = "2.0.0"
app = FastAPI(title="GreenLeaf IA — bacteriose da mandioca", version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

ACCEPTED_TYPES = {"image/jpeg", "image/jpg", "image/png"}
metrics = {"total_predictions": 0, "total_processing_time_ms": 0.0, "infected": 0}

try:
    predictor: Predictor | None = Predictor(config.MODEL_PATH, config.MODEL_META_PATH, tta=config.TTA)
    logger.info("Modelo %s carregado (%s).", predictor.version, config.MODEL_PATH.name)
except Exception:
    logger.exception("Modelo não carregou (%s); usando só a análise de cor.", config.MODEL_PATH)
    predictor = None

settings = DecisionSettings(
    threshold=config.CONFIDENCE_THRESHOLD,
    model_weight=config.MODEL_WEIGHT,
    min_infection_ratio=config.MIN_INFECTION_RATIO,
)

supabase_client = None
if config.SUPABASE_URL and config.SUPABASE_SERVICE_ROLE_KEY:
    try:
        from supabase import create_client

        supabase_client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
    except Exception:
        logger.exception("Supabase indisponível; histórico no servidor desligado.")


@app.get("/")
async def root() -> dict:
    return {"name": app.title, "docs": "/docs", "health": "/health"}


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": VERSION,
        "environment": config.APP_ENV,
        "model_loaded": predictor is not None,
        "supabase_logging": supabase_client is not None,
        "model_version": predictor.version if predictor else None,
    }


@app.get("/metrics")
async def get_metrics() -> dict:
    total = metrics["total_predictions"]
    return {
        "total_predictions": total,
        "infected_predictions": metrics["infected"],
        "average_processing_time_ms": round(metrics["total_processing_time_ms"] / total, 2) if total else 0,
    }


def _decode(contents: bytes) -> np.ndarray:
    try:
        with Image.open(BytesIO(contents)) as im:
            if im.format not in ("JPEG", "PNG"):
                raise HTTPException(status_code=400, detail="Envie uma foto JPG ou PNG.")
            im = ImageOps.exif_transpose(im).convert("RGB")
            return np.asarray(im)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Não foi possível abrir a imagem enviada.")


@app.post("/predict")
async def predict(image: UploadFile = File(...)) -> dict:
    started = time.perf_counter()
    if image.content_type not in ACCEPTED_TYPES:
        raise HTTPException(status_code=400, detail="Envie uma foto JPG ou PNG.")
    contents = await image.read(config.MAX_UPLOAD_BYTES + 1)
    if len(contents) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Imagem maior que {config.MAX_UPLOAD_MB} MB.")

    rgb = _decode(contents)
    try:
        check_quality(rgb)
    except ImageQualityError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    rgb = resize_max_side(rgb, config.ANALYSIS_MAX_SIDE)
    result = await run_in_threadpool(analyze, rgb, predictor, settings)
    elapsed = int((time.perf_counter() - started) * 1000)
    result["processing_time_ms"] = elapsed

    metrics["total_predictions"] += 1
    metrics["total_processing_time_ms"] += elapsed
    metrics["infected"] += result["class"] == "Infectado"

    if supabase_client is not None:
        try:
            supabase_client.table(config.SUPABASE_PREDICTION_TABLE).insert({
                "filename": image.filename,
                "content_type": image.content_type,
                "predicted_class": result["class"],
                "probability": result["probability"],
                "infection_ratio": result["ratio"],
                "severity": result["severity"],
                "processing_time_ms": elapsed,
            }).execute()
        except Exception:
            logger.exception("Falha ao gravar no Supabase.")
    return result

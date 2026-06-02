"""FastAPI server for cassava leaf blight detection."""

import base64
import logging
import time
from io import BytesIO

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

from config import (
    APP_ENV,
    CONFIDENCE_THRESHOLD,
    CORS_ORIGINS,
    MAX_UPLOAD_BYTES,
    MODEL_PATH,
    MODEL_WEIGHT,
    SUPABASE_PREDICTION_TABLE,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_URL,
)
from hsv_utils import classify_severity, create_overlay, segment_infection, segment_leaf
from logging_config import configure_logging
from model_utils_dl import load_trained_model, preprocess_image


configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Cassava Blight Detection API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metrics = {"total_predictions": 0, "total_processing_time_ms": 0.0}
supabase_client = None

try:
    model = load_trained_model(str(MODEL_PATH))
    if model is None:
        logger.warning("Model file not found at %s; using HSV-only fallback.", MODEL_PATH)
except Exception:
    logger.exception("Could not load model at %s. HSV fallback will be used.", MODEL_PATH)
    model = None

if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        from supabase import create_client

        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase prediction logging enabled.")
    except Exception:
        logger.exception("Supabase client could not be initialized; logging disabled.")


@app.get("/")
async def root() -> dict:
    return {"name": "Cassava Blight Detection API", "docs": "/docs", "health": "/health"}


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": app.version,
        "environment": APP_ENV,
        "model_loaded": model is not None,
        "supabase_logging": supabase_client is not None,
    }


@app.get("/metrics")
async def get_metrics() -> dict:
    total = metrics["total_predictions"]
    average = metrics["total_processing_time_ms"] / total if total else 0
    return {
        "total_predictions": total,
        "average_processing_time_ms": round(average, 2),
    }


@app.post("/predict")
async def predict(image: UploadFile = File(...)) -> JSONResponse:
    started = time.perf_counter()

    if image.content_type not in {"image/jpeg", "image/png", "image/jpg"}:
        raise HTTPException(status_code=400, detail="Formato de imagem nao suportado.")

    contents = await image.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Imagem muito grande para processamento.")

    try:
        pil_image = Image.open(BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Nao foi possivel abrir a imagem enviada.")

    np_image = np.array(pil_image)
    leaf_mask = segment_leaf(np_image)
    infection_mask = np.logical_and(leaf_mask, segment_infection(np_image))

    total_leaf_pixels = float(leaf_mask.sum()) if leaf_mask.sum() > 0 else 1.0
    ratio = float(infection_mask.sum() / total_leaf_pixels)
    severity = classify_severity(ratio)

    if model is not None:
        input_tensor = preprocess_image(pil_image)
        preds = model.predict(input_tensor, verbose=0)
        probability_model = float(preds[0][0])
        probability = (MODEL_WEIGHT * probability_model) + ((1 - MODEL_WEIGHT) * ratio)
    else:
        probability_model = None
        probability = ratio

    predicted_class = (
        "Infectado"
        if severity in {"Moderada", "Grave"} or probability >= CONFIDENCE_THRESHOLD
        else "Saudavel"
    )

    overlay_image = create_overlay(np_image, leaf_mask, infection_mask)
    success, buffer = cv2.imencode(".png", overlay_image)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao gerar overlay da imagem.")

    processing_time_ms = int((time.perf_counter() - started) * 1000)
    metrics["total_predictions"] += 1
    metrics["total_processing_time_ms"] += processing_time_ms

    payload = {
        "probability": probability,
        "model_probability": probability_model,
        "class": predicted_class,
        "ratio": ratio,
        "severity": severity,
        "processing_time_ms": processing_time_ms,
        "overlay": f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}",
    }

    if supabase_client is not None:
        try:
            supabase_client.table(SUPABASE_PREDICTION_TABLE).insert(
                {
                    "filename": image.filename,
                    "content_type": image.content_type,
                    "predicted_class": predicted_class,
                    "probability": probability,
                    "infection_ratio": ratio,
                    "severity": severity,
                    "processing_time_ms": processing_time_ms,
                }
            ).execute()
        except Exception:
            logger.exception("Could not write prediction log to Supabase.")

    return JSONResponse(content=payload)

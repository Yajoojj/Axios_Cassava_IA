from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env")
load_dotenv(PROJECT_DIR / ".env")


def _csv_env(name: str, default: str) -> List[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


APP_ENV = os.getenv("APP_ENV", "development")
PORT = _int_env("PORT", 8000)
CORS_ORIGINS = _csv_env(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
CONFIDENCE_THRESHOLD = _float_env("CONFIDENCE_THRESHOLD", 0.30)
MODEL_WEIGHT = min(max(_float_env("MODEL_WEIGHT", 0.50), 0.0), 1.0)
MAX_UPLOAD_MB = _int_env("MAX_UPLOAD_MB", 8)
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

_model_path = os.getenv("MODEL_PATH", "models/cassava_effnet.h5")
MODEL_PATH = Path(_model_path)
if not MODEL_PATH.is_absolute():
    MODEL_PATH = BASE_DIR / MODEL_PATH

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_PREDICTION_TABLE = os.getenv("SUPABASE_PREDICTION_TABLE", "prediction_logs")

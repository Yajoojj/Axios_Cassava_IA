from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parents[1]
load_dotenv(SERVER_DIR / ".env")


def _csv_env(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def _float_env(name: str, default: float | None) -> float | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _path_env(name: str, default: str) -> Path:
    path = Path(os.getenv(name, default))
    return path if path.is_absolute() else SERVER_DIR / path


APP_ENV = os.getenv("APP_ENV", "development")
CORS_ORIGINS = _csv_env(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://localhost:3000",
)
MAX_UPLOAD_MB = _int_env("MAX_UPLOAD_MB", 8)
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
# Lado maior da imagem usada na análise de cor e no overlay (a rede usa a própria entrada).
ANALYSIS_MAX_SIDE = _int_env("ANALYSIS_MAX_SIDE", 768)
TTA = os.getenv("TTA", "true").lower() in ("1", "true", "yes")

MODEL_PATH = _path_env("MODEL_PATH", "models/greenleaf_effb0.onnx")
MODEL_META_PATH = _path_env("MODEL_META_PATH", "models/greenleaf_effb0.json")


def _meta_value(key: str, default: float) -> float:
    try:
        return float(json.loads(MODEL_META_PATH.read_text(encoding="utf-8"))["decision"][key])
    except (OSError, KeyError, ValueError, TypeError):
        return default


# Limiar e peso vêm do arquivo de metadados (calibrados no conjunto de validação);
# as variáveis de ambiente só servem para sobrescrever.
CONFIDENCE_THRESHOLD = _float_env("CONFIDENCE_THRESHOLD", _meta_value("threshold", 0.5))
MODEL_WEIGHT = min(max(_float_env("MODEL_WEIGHT", _meta_value("model_weight", 1.0)), 0.0), 1.0)
MIN_INFECTION_RATIO = _float_env("MIN_INFECTION_RATIO", 0.02)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_PREDICTION_TABLE = os.getenv("SUPABASE_PREDICTION_TABLE", "prediction_logs")

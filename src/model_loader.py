"""Load the trained pipeline and metadata once, and verify that they agree."""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import joblib

from src.config import METADATA_PATH, MODEL_PATH

logger = logging.getLogger(__name__)


class ModelUnavailableError(RuntimeError):
    """The model artifact or its metadata cannot be used safely."""


@dataclass(frozen=True)
class LoadedModel:
    pipeline: Any
    metadata: dict


@lru_cache(maxsize=1)
def load_model() -> LoadedModel:
    """Load once per process. Never retrains and never substitutes another model."""
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise ModelUnavailableError(
            "Trained model files were not found. Run `python scripts/train_model.py` first.")
    try:
        metadata = json.loads(METADATA_PATH.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelUnavailableError("Model metadata could not be read.") from exc
    # Security: joblib/pickle can execute code. Verify the artifact's hash, recorded at
    # training time, before deserialising anything.
    expected_hash = metadata.get("artifact", {}).get("sha256")
    if not expected_hash:
        raise ModelUnavailableError("Model metadata has no artifact hash. Retrain the model.")
    try:
        actual_hash = hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()
    except OSError as exc:
        raise ModelUnavailableError("The model file could not be read.") from exc
    if actual_hash != expected_hash:
        logger.error("Model artifact hash mismatch; refusing to load")
        raise ModelUnavailableError(
            "The model file does not match its recorded hash. It may have been modified. "
            "Retrain the model from the training script.")

    try:
        pipeline = joblib.load(MODEL_PATH)
    except Exception as exc:
        logger.error("Model artifact failed to load: %s", type(exc).__name__)
        raise ModelUnavailableError("The model file could not be loaded.") from exc

    expected = metadata["feature_schema"]["order"]
    actual = list(getattr(pipeline, "feature_names_in_", []))
    if actual != expected:
        raise ModelUnavailableError(
            "The model and its metadata disagree on the feature schema. Retrain the model.")
    return LoadedModel(pipeline=pipeline, metadata=metadata)


def load_evaluation() -> dict:
    """Read the saved evaluation report. Raises ModelUnavailableError if missing or unreadable."""
    from src.config import ROOT
    path = ROOT / "models" / "evaluation_report.json"
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelUnavailableError("The evaluation report could not be read.") from exc

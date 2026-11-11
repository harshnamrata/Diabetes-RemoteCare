"""Individual screening: validate, run the saved model, return a structured result."""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from src.model_loader import ModelUnavailableError, load_model
from src.validation import to_model_frame, validate_individual

logger = logging.getLogger(__name__)

PREDICTION_FAILED = "The prediction could not be completed. Please check the entries and try again."


@dataclass(frozen=True)
class IndividualResult:
    status: str  # "ok" | "invalid" | "unavailable" | "error"
    flagged: bool = False
    probability: float | None = None
    threshold: float | None = None
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    message: str = ""


def screen_individual(record: dict) -> IndividualResult:
    try:
        loaded = load_model()
    except ModelUnavailableError as exc:
        return IndividualResult(status="unavailable", message=str(exc))

    schema = loaded.metadata["feature_schema"]
    validation = validate_individual(record, schema)
    if not validation.is_valid:
        return IndividualResult(status="invalid", errors=tuple(validation.errors),
                                warnings=tuple(validation.warnings))

    try:
        frame = to_model_frame(record, schema)
        probability = float(loaded.pipeline.predict_proba(frame)[0, 1])
    except Exception as exc:
        # Log the exception type only, never record values.
        logger.error("Individual prediction failed: %s", type(exc).__name__)
        return IndividualResult(status="error", message=PREDICTION_FAILED)

    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        logger.error("Model returned an invalid probability")
        return IndividualResult(status="error", message=PREDICTION_FAILED)

    threshold = float(loaded.metadata["training_config"]["decision_threshold"])
    return IndividualResult(
        status="ok",
        flagged=probability >= threshold,
        probability=probability,
        threshold=threshold,
        warnings=tuple(validation.warnings),
    )

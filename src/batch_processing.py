from __future__ import annotations

import io
import logging
import math
from dataclasses import dataclass, field

import pandas as pd

from src.model_loader import ModelUnavailableError, load_model
from src.regional_aggregation import summarize_regions
from src.validation import records_to_frame, validate_individual

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10_000
REGION_COL = "Region"
MAX_REGION_LEN = 64
NO_REGION = "(no region)"
ISSUE_COLUMNS = ["Row", "Region", "Severity", "Detail"]
RESULT_COLUMNS = ["Row", "Region", "Probability", "Flagged"]
SCORING_FAILED = "Batch scoring could not be completed. No results were produced."


@dataclass
class BatchResult:
    status: str
    message: str = ""
    total_rows: int = 0
    valid_rows: int = 0
    excluded_rows: int = 0
    flagged_rows: int = 0
    ignored_columns: list[str] = field(default_factory=list)
    issues: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=ISSUE_COLUMNS))
    results: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=RESULT_COLUMNS))
    summary: pd.DataFrame = field(default_factory=pd.DataFrame)


def _rejected(message: str) -> BatchResult:
    return BatchResult(status="rejected", message=message)


def process_batch(file_bytes: bytes, filename: str, sort_by: str = "count") -> BatchResult:
    if not filename.lower().endswith(".csv"):
        return _rejected("Only .csv files are accepted.")
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        return _rejected(f"The file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    if not file_bytes.strip():
        return _rejected("The file is empty.")
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        return _rejected("The file must be UTF-8 encoded CSV.")
    try:
        df = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    except (pd.errors.ParserError, pd.errors.EmptyDataError):
        return _rejected("The file could not be read as CSV. Check its structure.")
    df.columns = [str(c).strip() for c in df.columns]
    if df.empty:
        return _rejected("The file has a header but no records.")
    if len(df) > MAX_ROWS:
        return _rejected(f"The file has {len(df):,} rows; the limit is {MAX_ROWS:,}.")

    try:
        loaded = load_model()
    except ModelUnavailableError as exc:
        return BatchResult(status="unavailable", message=str(exc))
    schema = loaded.metadata["feature_schema"]
    threshold = float(loaded.metadata["training_config"]["decision_threshold"])

    required = [REGION_COL] + schema["order"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return _rejected("Missing required columns: " + ", ".join(missing) + ".")
    ignored = [c for c in df.columns if c not in required]
    df = df[required].apply(lambda s: s.str.strip())

    issues: list[dict] = []
    all_rows: list[dict] = []
    valid_features: list[dict] = []
    valid_meta: list[tuple[int, str]] = []
    first_seen: dict[tuple, int] = {}

    for position, (_, row) in enumerate(df.iterrows()):
        row_number = position + 2
        region_raw = row[REGION_COL]
        region = region_raw if region_raw else NO_REGION
        errors: list[str] = []
        warnings: list[str] = []

        if not region_raw:
            errors.append("Region is missing.")
        elif len(region_raw) > MAX_REGION_LEN:
            errors.append(f"Region is longer than {MAX_REGION_LEN} characters.")

        key = tuple(row[c] for c in required)
        if key in first_seen:
            errors.append(f"Duplicate of row {first_seen[key]}; excluded to avoid double counting.")
        else:
            first_seen[key] = row_number

        features = {c: row[c] for c in schema["order"]}
        check = validate_individual(features, schema)
        errors += check.errors
        warnings += check.warnings

        excluded = bool(errors)
        for msg in errors:
            issues.append({"Row": row_number, "Region": region, "Severity": "Excluded", "Detail": msg})
        for msg in warnings:
            issues.append({"Row": row_number, "Region": region, "Severity": "Warning",
                           "Detail": msg + " Row was still scored."})
        all_rows.append({"Region": region, "excluded": excluded})
        if not excluded:
            valid_features.append(features)
            valid_meta.append((row_number, region))

    probs: list[float] = []
    if valid_features:
        try:
            frame = records_to_frame(valid_features, schema)
            probs = [float(p) for p in loaded.pipeline.predict_proba(frame)[:, 1]]
        except Exception as exc:
            logger.error("Batch prediction failed: %s", type(exc).__name__)
            return BatchResult(status="error", message=SCORING_FAILED)
        if not all(math.isfinite(p) and 0.0 <= p <= 1.0 for p in probs):
            logger.error("Batch model returned invalid probabilities")
            return BatchResult(status="error", message=SCORING_FAILED)

    flags = [p >= threshold for p in probs]
    results = pd.DataFrame({
        "Row": [m[0] for m in valid_meta],
        "Region": [m[1] for m in valid_meta],
        "Probability": probs,
        "Flagged": flags,
    }, columns=RESULT_COLUMNS)

    summary = summarize_regions(
        results[["Region", "Flagged"]],
        pd.DataFrame(all_rows, columns=["Region", "excluded"]),
        sort_by=sort_by,
    )

    valid_count = len(valid_features)
    excluded_count = sum(r["excluded"] for r in all_rows)
    message = (f"Scored {valid_count:,} of {len(df):,} rows. "
               f"{excluded_count:,} row(s) excluded.")
    if ignored:
        message += f" Ignored extra columns: {', '.join(ignored)}."

    return BatchResult(
        status="ok",
        message=message,
        total_rows=len(df),
        valid_rows=valid_count,
        excluded_rows=excluded_count,
        flagged_rows=int(sum(flags)),
        ignored_columns=ignored,
        issues=pd.DataFrame(issues, columns=ISSUE_COLUMNS),
        results=results,
        summary=summary,
    )

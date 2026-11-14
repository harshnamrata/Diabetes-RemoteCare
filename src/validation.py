"""Input validation at the application boundary (individual and batch records)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd

from src.config import ENTRY_LIMITS, WHOLE_NUMBER_FIELDS


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_individual(record: dict, schema: dict) -> ValidationResult:
    """Errors block prediction. Warnings (outside training range) do not."""
    res = ValidationResult()
    numeric = schema["numeric"]
    categorical = schema["categorical"]
    ranges = schema.get("ranges", {})
    values: dict = {}

    for col in schema["order"]:
        raw = record.get(col)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            res.errors.append(f"{col} is required.")
            continue

        if col in numeric:
            try:
                num = float(raw)
            except (TypeError, ValueError):
                res.errors.append(f"{col} must be a number.")
                continue
            if not math.isfinite(num):
                res.errors.append(f"{col} must be a finite number.")
                continue
            if col in WHOLE_NUMBER_FIELDS and not num.is_integer():
                res.errors.append(f"{col} must be a whole number.")
                continue
            lo, hi = ENTRY_LIMITS[col]
            if not lo <= num <= hi:
                res.errors.append(f"{col} must be between {lo:g} and {hi:g}.")
                continue
            values[col] = num
            if col in ranges:
                tlo, thi = ranges[col]
                if not tlo <= num <= thi:
                    res.warnings.append(
                        f"{col} ({num:g}) is outside the range seen in the training data "
                        f"({tlo:g} to {thi:g}). The result may be less reliable.")
        else:
            options = categorical[col]
            if str(raw) not in options:
                res.errors.append(f"{col} must be one of: {', '.join(options)}.")
                continue
            values[col] = str(raw)

    if not res.errors and values.get("Gender") == "Male" and values.get("Pregnancies", 0) > 0:
        res.errors.append("Pregnancies must be 0 when Gender is Male.")
    return res


def records_to_frame(records: list[dict], schema: dict) -> pd.DataFrame:
    """Build a DataFrame with exactly the training column order and types."""
    rows = [{col: (float(r[col]) if col in schema["numeric"] else str(r[col]))
             for col in schema["order"]} for r in records]
    return pd.DataFrame(rows, columns=schema["order"])


def to_model_frame(record: dict, schema: dict) -> pd.DataFrame:
    return records_to_frame([record], schema)

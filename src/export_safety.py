from __future__ import annotations

import pandas as pd

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def neutralise_cell(value):
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def to_safe_csv_bytes(df: pd.DataFrame) -> bytes:
    out = df.copy()
    for col in out.columns:
        if out[col].dtype == object or pd.api.types.is_string_dtype(out[col]):
            out[col] = out[col].map(neutralise_cell)
    return out.to_csv(index=False).encode("utf-8")

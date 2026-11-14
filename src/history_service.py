"""
Session-only screening history.

Stores aggregate counts per operation only: no names, IDs, region-level patient data,
or feature values. Nothing here is written to disk.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pandas as pd

MAX_HISTORY = 200
HISTORY_COLUMNS = ["Timestamp (UTC)", "Mode", "Records received", "Records scored",
                   "Records flagged", "Status"]
INDIVIDUAL = "Individual screening"
BATCH = "Regional batch"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_entry(mode: str, received: int, scored: int, flagged: int, status: str,
               timestamp: str | None = None) -> dict:
    return {
        "Timestamp (UTC)": timestamp or _now(),
        "Mode": mode,
        "Records received": int(received),
        "Records scored": int(scored),
        "Records flagged": int(flagged),
        "Status": status,
    }


def individual_entry(status: str, flagged: bool = False) -> dict | None:
    if status == "ok":
        return make_entry(INDIVIDUAL, 1, 1, int(flagged), "Completed")
    if status == "invalid":
        return make_entry(INDIVIDUAL, 1, 0, 0, "Rejected")
    if status == "error":
        return make_entry(INDIVIDUAL, 1, 0, 0, "Error")
    return None  # model unavailable: no screening took place


def batch_entry(result) -> dict | None:
    """result: a BatchResult from src.batch_processing."""
    if result.status == "ok":
        return make_entry(BATCH, result.total_rows, result.valid_rows,
                          result.flagged_rows, "Completed")
    if result.status == "rejected":
        return make_entry(BATCH, 0, 0, 0, "Rejected")
    if result.status == "error":
        return make_entry(BATCH, result.total_rows, 0, 0, "Error")
    return None


def append_entry(history: list[dict], entry: dict | None) -> list[dict]:
    if entry is None:
        return list(history)
    return (list(history) + [entry])[-MAX_HISTORY:]


def session_totals(history: list[dict]) -> dict:
    completed = [e for e in history if e["Status"] == "Completed"]
    return {
        "operations": len(history),
        "completed": len(completed),
        "records_scored": sum(e["Records scored"] for e in completed),
        "records_flagged": sum(e["Records flagged"] for e in completed),
    }


def history_frame(history: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(history, columns=HISTORY_COLUMNS)


def upload_fingerprint(data: bytes) -> str:
    """Identifies an upload so reruns (e.g. changing the sort) are not logged twice."""
    return hashlib.sha256(data).hexdigest()


def should_log_batch(stored_fingerprint: str | None, new_fingerprint: str) -> bool:
    return stored_fingerprint != new_fingerprint


def batch_snapshot(result, generated_at: str | None = None) -> dict:
    """Aggregate-only copy of the latest regional batch, for the dashboard and report."""
    return {
        "summary": result.summary.copy(),
        "received": result.total_rows,
        "scored": result.valid_rows,
        "flagged": result.flagged_rows,
        "excluded": result.excluded_rows,
        "timestamp": generated_at or _now(),
    }

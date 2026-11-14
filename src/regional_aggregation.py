"""Aggregate model predictions by region. Ranking uses actual classifier outputs only."""
from __future__ import annotations

import pandas as pd

SMALL_SAMPLE_THRESHOLD = 30
SORT_OPTIONS = ("count", "percent")


def summarize_regions(scored: pd.DataFrame, all_rows: pd.DataFrame,
                      sort_by: str = "count",
                      small_sample_threshold: int = SMALL_SAMPLE_THRESHOLD) -> pd.DataFrame:
    """
    scored:   one row per valid, scored record. Columns: Region, Flagged (bool).
    all_rows: one row per uploaded record. Columns: Region, excluded (bool).
    Regions with zero valid records are kept, with At-risk % left blank (NaN).
    """
    if sort_by not in SORT_OPTIONS:
        raise ValueError(f"sort_by must be one of {SORT_OPTIONS}")

    # Enforce columns and dtypes so empty inputs (e.g. every row excluded) still aggregate.
    scored = scored.reindex(columns=["Region", "Flagged"]).astype({"Region": object, "Flagged": bool})
    all_rows = all_rows.reindex(columns=["Region", "excluded"]).astype(
        {"Region": object, "excluded": bool})

    regions = pd.Index(all_rows["Region"].unique())
    valid = scored.groupby("Region").size().reindex(regions, fill_value=0)
    flagged = (scored[scored["Flagged"]].groupby("Region").size()
               .reindex(regions, fill_value=0))
    excluded = (all_rows[all_rows["excluded"]].groupby("Region").size()
                .reindex(regions, fill_value=0))

    percent = (flagged / valid.where(valid > 0) * 100).round(1)

    out = pd.DataFrame({
        "Region": regions,
        "Total valid records": valid.to_numpy(),
        "Flagged as higher risk": flagged.to_numpy(),
        "At-risk %": percent.to_numpy(),
        "Invalid rows excluded": excluded.to_numpy(),
    })
    out["Small sample"] = out["Total valid records"] < small_sample_threshold

    if sort_by == "percent":
        out = out.sort_values(["At-risk %", "Flagged as higher risk", "Region"],
                              ascending=[False, False, True], na_position="last")
    else:
        out = out.sort_values(["Flagged as higher risk", "At-risk %", "Region"],
                              ascending=[False, False, True], na_position="last")
    out.insert(0, "Rank", range(1, len(out) + 1))
    return out.reset_index(drop=True)

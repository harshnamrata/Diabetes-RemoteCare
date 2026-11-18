from __future__ import annotations

import pandas as pd

SMALL_SAMPLE_THRESHOLD = 30
RANK_OPTIONS = {"Flagged count": "count", "At-risk percentage": "percent"}


def rank_summary(summary: pd.DataFrame, by: str) -> pd.DataFrame:
    if by == "count":
        cols = ["Flagged as higher risk", "At-risk %", "Region"]
    elif by == "percent":
        cols = ["At-risk %", "Flagged as higher risk", "Region"]
    else:
        raise ValueError("by must be 'count' or 'percent'")
    out = summary.drop(columns=["Rank"], errors="ignore")
    out = out.sort_values(cols, ascending=[False, False, True], na_position="last")
    out = out.reset_index(drop=True)
    out.insert(0, "Rank", range(1, len(out) + 1))
    return out


def summarize_regions(scored: pd.DataFrame, all_rows: pd.DataFrame,
                      sort_by: str = "count",
                      small_sample_threshold: int = SMALL_SAMPLE_THRESHOLD) -> pd.DataFrame:
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
    return rank_summary(out, sort_by)

import math

import pandas as pd
import pytest

import src.batch_processing as batch
from src.batch_processing import process_batch
from src.config import ROOT
from tests.sample_record import SAMPLE as DEFAULTS
from src.model_loader import ModelUnavailableError
from src.regional_aggregation import summarize_regions

DEMO = ROOT / "data" / "sample" / "SYNTHETIC_regional_demo.csv"


def good(region="North", **kw):
    return {"Region": region, **DEFAULTS, **kw}


def make_csv(rows):
    return pd.DataFrame(rows).to_csv(index=False).encode()


def test_rejects_non_csv():
    assert process_batch(b"a,b", "data.xlsx").status == "rejected"


def test_rejects_oversize(monkeypatch):
    monkeypatch.setattr(batch, "MAX_UPLOAD_BYTES", 10)
    assert "larger than" in process_batch(make_csv([good()]), "a.csv").message


def test_rejects_empty_file():
    assert process_batch(b"", "a.csv").status == "rejected"


def test_rejects_non_utf8():
    assert "UTF-8" in process_batch(b"\x80\x81\x82", "a.csv").message


def test_rejects_missing_columns():
    result = process_batch(b"Region,Age\nNorth,40\n", "a.csv")
    assert result.status == "rejected"
    assert "Missing required columns" in result.message


def test_rejects_header_only():
    header = ",".join(["Region"] + list(DEFAULTS)).encode() + b"\n"
    assert "no records" in process_batch(header, "a.csv").message


def test_rejects_too_many_rows(monkeypatch):
    monkeypatch.setattr(batch, "MAX_ROWS", 2)
    assert "limit is 2" in process_batch(make_csv([good()] * 3), "a.csv").message


def test_model_unavailable_is_reported(monkeypatch):
    def fail():
        raise ModelUnavailableError("missing for test")
    monkeypatch.setattr(batch, "load_model", fail)
    assert process_batch(make_csv([good()]), "a.csv").status == "unavailable"


def test_valid_file_scores_every_row():
    rows = [good("North"), good("North", BMI=30.0), good("South")]
    result = process_batch(make_csv(rows), "a.csv")
    assert result.status == "ok"
    assert result.total_rows == 3 and result.valid_rows == 3 and result.excluded_rows == 0
    assert len(result.results) == 3
    assert result.results["Probability"].between(0, 1).all()


def test_counts_are_consistent():
    rows = [good(), good(BMI="abc"), good(), good(Region="")]
    result = process_batch(make_csv(rows), "a.csv")
    assert result.valid_rows + result.excluded_rows == result.total_rows == 4
    assert result.valid_rows == len(result.results)


def test_invalid_row_is_excluded_and_reported_with_line_number():
    result = process_batch(make_csv([good(), good(BMI="abc"), good("South")]), "a.csv")
    excluded = result.issues[result.issues["Severity"] == "Excluded"]
    assert list(excluded["Row"]) == [3]
    assert "BMI must be a number." in excluded["Detail"].iloc[0]
    assert result.valid_rows == 2


def test_blank_region_is_excluded():
    result = process_batch(make_csv([good(Region="")]), "a.csv")
    assert result.valid_rows == 0
    assert "Region is missing." in result.issues["Detail"].iloc[0]
    assert "(no region)" in set(result.summary["Region"])


def test_duplicate_rows_are_excluded():
    result = process_batch(make_csv([good("North"), good("North")]), "a.csv")
    assert result.valid_rows == 1 and result.excluded_rows == 1
    assert "Duplicate of row 2" in result.issues["Detail"].iloc[0]


def test_same_features_in_different_region_are_not_duplicates():
    assert process_batch(make_csv([good("North"), good("South")]), "a.csv").valid_rows == 2


def test_extra_columns_are_ignored_and_reported():
    result = process_batch(make_csv([{**good(), "Diabetic": "Yes"}]), "a.csv")
    assert result.status == "ok"
    assert result.ignored_columns == ["Diabetic"]


def test_column_order_does_not_matter():
    rows = [dict(reversed(list(good().items())))]
    assert process_batch(make_csv(rows), "a.csv").valid_rows == 1


def test_outside_range_row_is_scored_with_warning():
    result = process_batch(make_csv([good(BMI=45.0)]), "a.csv")
    assert result.valid_rows == 1
    assert (result.issues["Severity"] == "Warning").any()


def test_all_rows_invalid_returns_ok_with_no_results():
    result = process_batch(make_csv([good(BMI="abc")]), "a.csv")
    assert result.status == "ok" and result.valid_rows == 0
    assert result.results.empty


def test_batch_uses_same_model_as_individual_screening():
    from src.prediction_service import screen_individual
    single = screen_individual(DEFAULTS)
    result = process_batch(make_csv([good("North")]), "a.csv")
    assert math.isclose(result.results["Probability"].iloc[0], single.probability, rel_tol=1e-9)


def test_demo_file_processes_with_expected_problems():
    result = process_batch(DEMO.read_bytes(), DEMO.name)
    assert result.status == "ok"
    assert result.excluded_rows >= 5
    details = " ".join(result.issues["Detail"])
    assert "Duplicate of row" in details
    assert "Region is missing." in details
    assert "Pregnancies must be 0 when Gender is Male." in details
    assert (result.issues["Severity"] == "Warning").any()


def _scored(pairs):
    return pd.DataFrame(pairs, columns=["Region", "Flagged"])


def _all(pairs):
    return pd.DataFrame(pairs, columns=["Region", "excluded"])


def test_percentage_calculation():
    scored = _scored([("A", True), ("A", False), ("A", False), ("A", False)])
    row = summarize_regions(scored, _all([("A", False)] * 4)).iloc[0]
    assert row["Flagged as higher risk"] == 1
    assert row["At-risk %"] == 25.0


def test_zero_valid_region_is_safe():
    scored = _scored([("A", True)])
    all_rows = _all([("A", False), ("B", True), ("B", True)])
    s = summarize_regions(scored, all_rows).set_index("Region")
    assert s.loc["B", "Total valid records"] == 0
    assert math.isnan(s.loc["B", "At-risk %"])
    assert s.loc["B", "Invalid rows excluded"] == 2


def test_count_and_percent_rank_differently():
    scored = _scored([("A", True)] * 5 + [("A", False)] * 45 + [("B", True)] * 2)
    all_rows = _all([("A", False)] * 50 + [("B", False)] * 2)
    assert summarize_regions(scored, all_rows, sort_by="count").iloc[0]["Region"] == "A"
    assert summarize_regions(scored, all_rows, sort_by="percent").iloc[0]["Region"] == "B"


def test_small_sample_flag():
    s = summarize_regions(_scored([("A", True)] * 3), _all([("A", False)] * 3)).iloc[0]
    assert bool(s["Small sample"]) is True


def test_rank_column_and_totals_are_consistent():
    scored = _scored([("A", True), ("B", False), ("C", True), ("C", False)])
    all_rows = _all([("A", False), ("B", False), ("C", False), ("C", False), ("D", True)])
    s = summarize_regions(scored, all_rows)
    assert list(s["Rank"]) == list(range(1, len(s) + 1))
    assert s["Total valid records"].sum() == len(scored)
    assert s["Invalid rows excluded"].sum() == 1
    assert s["Flagged as higher risk"].sum() == scored["Flagged"].sum()


def test_invalid_sort_option_rejected():
    with pytest.raises(ValueError):
        summarize_regions(_scored([("A", True)]), _all([("A", False)]), sort_by="bogus")

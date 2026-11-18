import pandas as pd
import pytest

from src.history_service import (HISTORY_COLUMNS, MAX_HISTORY, append_entry, batch_entry,
                                 batch_snapshot, history_frame, individual_entry, make_entry,
                                 session_totals, should_log_batch, upload_fingerprint)
from src.report_generator import build_markdown_report


class _Batch:
    def __init__(self, status, total=0, valid=0, flagged=0):
        self.status, self.total_rows, self.valid_rows, self.flagged_rows = status, total, valid, flagged


def test_entry_has_only_aggregate_fields():
    e = make_entry("Individual screening", 1, 1, 0, "Completed")
    assert list(e) == HISTORY_COLUMNS


def test_individual_status_mapping():
    assert individual_entry("ok", flagged=True)["Records flagged"] == 1
    assert individual_entry("invalid")["Status"] == "Rejected"
    assert individual_entry("error")["Status"] == "Error"
    assert individual_entry("unavailable") is None


def test_batch_status_mapping():
    assert batch_entry(_Batch("ok", 400, 394, 173))["Records scored"] == 394
    assert batch_entry(_Batch("rejected"))["Records received"] == 0
    assert batch_entry(_Batch("unavailable")) is None


def test_totals_count_only_completed_operations():
    h = [make_entry("a", 1, 1, 1, "Completed"), make_entry("a", 1, 0, 0, "Rejected"),
         make_entry("b", 10, 9, 4, "Completed")]
    t = session_totals(h)
    assert t["operations"] == 3 and t["completed"] == 2
    assert t["records_scored"] == 10 and t["records_flagged"] == 5


def test_history_is_capped():
    h = []
    for _ in range(MAX_HISTORY + 5):
        h = append_entry(h, make_entry("a", 1, 1, 0, "Completed"))
    assert len(h) == MAX_HISTORY


def test_append_none_is_noop():
    assert append_entry([], None) == []


def test_empty_history_frame_has_columns():
    assert list(history_frame([]).columns) == HISTORY_COLUMNS


def test_fingerprint_prevents_double_logging_on_rerun():
    fp = upload_fingerprint(b"same bytes")
    assert should_log_batch(None, fp)
    assert not should_log_batch(fp, upload_fingerprint(b"same bytes"))
    assert should_log_batch(fp, upload_fingerprint(b"other bytes"))


def test_batch_snapshot_is_aggregate_only():
    class R:
        summary = pd.DataFrame({"Rank": [1], "Region": ["A"], "Flagged as higher risk": [2]})
        total_rows, valid_rows, flagged_rows, excluded_rows = 5, 4, 2, 1
    snap = batch_snapshot(R(), "2026-01-01T00:00:00+00:00")
    assert set(snap) == {"summary", "received", "scored", "flagged", "excluded", "timestamp"}


@pytest.fixture
def meta_and_eval(schema):
    import json
    from src.config import METADATA_PATH
    from src.model_loader import load_evaluation
    meta = json.loads(METADATA_PATH.read_text())
    return meta, load_evaluation()


def test_report_contains_required_sections(meta_and_eval):
    meta, ev = meta_and_eval
    text = build_markdown_report(meta, ev, [], None, "2026-01-01T00:00:00+00:00")
    for heading in ["## 1. Model and dataset", "## 2. Evaluation summary",
                    "## 3. Session screening summary", "## 4. Session history",
                    "## 5. Regional ranking", "## 6. Limitations"]:
        assert heading in text
    assert "No screening operations were recorded this session." in text
    assert "No regional batch was processed this session." in text
    assert "SYNTHETIC" in text.upper()


def test_report_sanitises_region_names_and_includes_snapshot(meta_and_eval):
    meta, ev = meta_and_eval
    summary = pd.DataFrame({"Rank": [1], "Region": ["Bad | name\nx"],
                            "Total valid records": [3], "At-risk %": [float("nan")]})
    snap = {"summary": summary, "received": 4, "scored": 3, "flagged": 0,
            "excluded": 1, "timestamp": "t"}
    text = build_markdown_report(meta, ev, [make_entry("Regional batch", 4, 3, 0, "Completed")],
                                 snap, "t")
    assert "Bad / name x" in text
    assert "n/a" in text
    assert "Regional batch" in text

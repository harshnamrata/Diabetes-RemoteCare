import json

import pandas as pd
import pytest

import src.model_loader as model_loader
from src.batch_processing import process_batch
from src.config import METADATA_PATH
from src.config import MODEL_PATH
from tests.sample_record import SAMPLE as DEFAULTS
from src.export_safety import neutralise_cell, to_safe_csv_bytes
from src.model_loader import ModelUnavailableError
from src.report_generator import build_markdown_report


@pytest.mark.parametrize("value", ["=HYPERLINK(\"x\")", "+1+1", "-2", "@SUM(A1)", "\tcmd"])
def test_formula_prefixes_are_neutralised(value):
    assert neutralise_cell(value).startswith("'")


def test_normal_text_and_numbers_untouched():
    assert neutralise_cell("Region A") == "Region A"
    assert neutralise_cell(3.5) == 3.5


def test_safe_csv_neutralises_region_names_in_export():
    df = pd.DataFrame({"Region": ["=cmd|' /C calc'!A0", "North"], "Count": [1, 2]})
    text = to_safe_csv_bytes(df).decode()
    assert "'=cmd" in text
    assert text.splitlines()[2].startswith("North,")


def test_region_with_formula_is_handled_in_batch_and_export():
    row = {"Region": "=1+1", **DEFAULTS}
    result = process_batch(pd.DataFrame([row]).to_csv(index=False).encode(), "a.csv")
    assert result.status == "ok"
    exported = to_safe_csv_bytes(result.summary).decode()
    assert "'=1+1" in exported


def test_tampered_artifact_is_refused(tmp_path, monkeypatch):
    tampered = tmp_path / "model.joblib"
    tampered.write_bytes(MODEL_PATH.read_bytes() + b"tamper")
    monkeypatch.setattr(model_loader, "MODEL_PATH", tampered)
    with pytest.raises(ModelUnavailableError, match="does not match its recorded hash"):
        model_loader.load_model.__wrapped__()


def test_metadata_without_artifact_hash_is_refused(tmp_path, monkeypatch):
    meta = json.loads(METADATA_PATH.read_text())
    meta.pop("artifact", None)
    path = tmp_path / "meta.json"
    path.write_text(json.dumps(meta))
    monkeypatch.setattr(model_loader, "METADATA_PATH", path)
    with pytest.raises(ModelUnavailableError, match="no artifact hash"):
        model_loader.load_model.__wrapped__()


def test_recorded_hash_matches_artifact_on_disk():
    import hashlib
    meta = json.loads(METADATA_PATH.read_text())
    assert hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest() == meta["artifact"]["sha256"]


def test_processed_results_export_has_no_health_values():
    row = {"Region": "North", **DEFAULTS}
    result = process_batch(pd.DataFrame([row]).to_csv(index=False).encode(), "a.csv")
    assert list(result.results.columns) == ["Row", "Region", "Probability", "Flagged"]


def test_report_contains_no_feature_values():
    from src.config import METADATA_PATH as MP
    from src.model_loader import load_evaluation
    meta = json.loads(MP.read_text())
    text = build_markdown_report(meta, load_evaluation(), [], None, "t")
    assert "more than half an hour" not in text
    assert "Occasionally" not in text


def test_user_region_text_cannot_inject_links_into_report():
    from src.config import METADATA_PATH as MP
    from src.model_loader import load_evaluation
    meta = json.loads(MP.read_text())
    summary = pd.DataFrame({"Rank": [1], "Region": ["[click](http://x.example)<img src=x>"],
                            "Total valid records": [1]})
    snap = {"summary": summary, "received": 1, "scored": 1, "flagged": 0, "excluded": 0,
            "timestamp": "t"}
    text = build_markdown_report(meta, load_evaluation(), [], snap, "t")
    assert "[click]" not in text and "<img" not in text


def test_streamlit_config_sets_upload_limit_and_disables_telemetry():
    import tomllib
    from src.config import ROOT
    cfg = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())
    assert cfg["server"]["maxUploadSize"] == 5
    assert cfg["browser"]["gatherUsageStats"] is False

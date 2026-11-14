"""Failure paths that the coverage report showed as untested."""
import pandas as pd
import pytest

import src.batch_processing as batch
import src.model_loader as model_loader
from src.batch_processing import process_batch
from src.config import DEFAULTS
from src.model_loader import LoadedModel, ModelUnavailableError, load_evaluation, load_model
from src.prediction_service import screen_individual


def good(region="North", **kw):
    return {"Region": region, **DEFAULTS, **kw}


def csv(rows):
    return pd.DataFrame(rows).to_csv(index=False).encode()


class _Pipe:
    def __init__(self, exc=None, probs=None):
        self.exc, self.probs = exc, probs

    def predict_proba(self, X):
        if self.exc:
            raise self.exc
        return self.probs


def _fake(pipe):
    real = load_model()
    return lambda: LoadedModel(pipeline=pipe, metadata=real.metadata)


# ---------- model loader ----------

def test_missing_model_files_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(model_loader, "MODEL_PATH", tmp_path / "none.joblib")
    with pytest.raises(ModelUnavailableError, match="not found"):
        model_loader.load_model.__wrapped__()


def test_corrupt_metadata_reported(tmp_path, monkeypatch):
    bad = tmp_path / "meta.json"
    bad.write_text("{not json")
    monkeypatch.setattr(model_loader, "METADATA_PATH", bad)
    with pytest.raises(ModelUnavailableError, match="metadata could not be read"):
        model_loader.load_model.__wrapped__()


def test_unreadable_artifact_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(model_loader, "MODEL_PATH", tmp_path)  # a directory, not a file
    with pytest.raises(ModelUnavailableError, match="could not be read"):
        model_loader.load_model.__wrapped__()


def test_evaluation_report_missing_reported(tmp_path, monkeypatch):
    from src import config
    monkeypatch.setattr(config, "ROOT", tmp_path)
    with pytest.raises(ModelUnavailableError, match="evaluation report"):
        load_evaluation()


# ---------- batch edge cases ----------

def test_bom_only_file_is_rejected_as_unreadable():
    result = process_batch(b"\xef\xbb\xbf", "a.csv")
    assert result.status == "rejected"


def test_region_longer_than_limit_is_excluded():
    result = process_batch(csv([good("R" * 65)]), "a.csv")
    assert result.valid_rows == 0
    assert "longer than 64" in result.issues["Detail"].iloc[0]


def test_scoring_exception_produces_error_not_results(monkeypatch):
    monkeypatch.setattr(batch, "load_model", _fake(_Pipe(exc=RuntimeError("boom"))))
    result = process_batch(csv([good()]), "a.csv")
    assert result.status == "error"
    assert result.results.empty
    assert "No results were produced" in result.message


def test_invalid_batch_probabilities_produce_error(monkeypatch):
    monkeypatch.setattr(batch, "load_model", _fake(_Pipe(probs=[[1.7]])))
    result = process_batch(csv([good()]), "a.csv")
    assert result.status == "error"


def test_individual_prediction_exception_is_graceful(monkeypatch):
    import src.prediction_service as service
    monkeypatch.setattr(service, "load_model", _fake(_Pipe(exc=ValueError("x"))))
    assert screen_individual(DEFAULTS).status == "error"

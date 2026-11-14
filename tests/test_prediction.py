import pytest

import src.model_loader as model_loader
import src.prediction_service as service
from src.config import DEFAULTS, METADATA_PATH
from src.model_loader import ModelUnavailableError, load_model
from src.prediction_service import screen_individual


def test_pipeline_feature_order_matches_metadata(schema):
    loaded = load_model()
    assert list(loaded.pipeline.feature_names_in_) == schema["order"]


def test_valid_record_returns_probability_and_consistent_flag():
    result = screen_individual(DEFAULTS)
    assert result.status == "ok"
    assert 0.0 <= result.probability <= 1.0
    assert result.flagged == (result.probability >= result.threshold)


def test_prediction_is_deterministic():
    a = screen_individual(DEFAULTS)
    b = screen_individual(DEFAULTS)
    assert a.probability == b.probability


def test_invalid_record_is_not_scored():
    result = screen_individual({**DEFAULTS, "BMI": "abc"})
    assert result.status == "invalid"
    assert result.probability is None
    assert "BMI must be a number." in result.errors


def test_model_unavailable_is_reported(monkeypatch):
    def fail():
        raise ModelUnavailableError("Model missing for test.")
    monkeypatch.setattr(service, "load_model", fail)
    result = screen_individual(DEFAULTS)
    assert result.status == "unavailable"
    assert result.message == "Model missing for test."


class _BrokenPipeline:
    feature_names_in_ = None

    def predict_proba(self, _):
        raise RuntimeError("boom")


class _OutOfRangePipeline:
    def predict_proba(self, X):
        return [[-0.5, 1.5]]


def _fake_loader(pipeline):
    real = load_model()
    from src.model_loader import LoadedModel
    return lambda: LoadedModel(pipeline=pipeline, metadata=real.metadata)


def test_prediction_failure_is_graceful_and_leaks_no_values(monkeypatch, caplog):
    monkeypatch.setattr(service, "load_model", _fake_loader(_BrokenPipeline()))
    with caplog.at_level("ERROR"):
        result = screen_individual(DEFAULTS)
    assert result.status == "error"
    assert result.probability is None
    assert result.message == service.PREDICTION_FAILED
    assert "Female" not in caplog.text and "25.0" not in caplog.text


def test_invalid_probability_is_rejected(monkeypatch):
    monkeypatch.setattr(service, "load_model", _fake_loader(_OutOfRangePipeline()))
    result = screen_individual(DEFAULTS)
    assert result.status == "error"


def test_schema_mismatch_is_refused(tmp_path, monkeypatch):
    import json
    bad = json.loads(METADATA_PATH.read_text())
    bad["feature_schema"]["order"] = list(reversed(bad["feature_schema"]["order"]))
    bad_path = tmp_path / "meta.json"
    bad_path.write_text(json.dumps(bad))
    monkeypatch.setattr(model_loader, "METADATA_PATH", bad_path)
    with pytest.raises(ModelUnavailableError, match="disagree on the feature schema"):
        model_loader.load_model.__wrapped__()

import sys

import pandas as pd
import pytest

from src.config import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import train_model


def test_validate_rejects_unexpected_labels():
    df = pd.DataFrame({"Diabetic": ["Yes", "Maybe"], "x": [1, 2]})
    with pytest.raises(ValueError, match="unexpected target labels"):
        train_model.validate(df)


def test_validate_rejects_missing_target():
    with pytest.raises(ValueError, match="target column missing"):
        train_model.validate(pd.DataFrame({"x": [1]}))


def test_validate_rejects_missing_values():
    df = pd.DataFrame({"Diabetic": ["Yes", "No"], "x": [1, None]})
    with pytest.raises(ValueError, match="missing values"):
        train_model.validate(df)


def test_validate_accepts_real_dataset():
    df = pd.read_csv(ROOT / "data" / "sample" / "synthetic_diabetes_2019.csv")
    info = train_model.validate(df)
    assert info["rows"] == len(df) and info["missing_values"] == 0


def test_demo_file_has_expected_shape():
    demo = pd.read_csv(ROOT / "data" / "sample" / "SYNTHETIC_regional_demo.csv", dtype=str,
                       keep_default_na=False)
    assert len(demo) == 400
    assert demo.columns[0] == "Region"
    assert "Diabetic" not in demo.columns

import math

from src.config import DEFAULTS, ENTRY_LIMITS
from src.validation import validate_individual


def rec(**overrides):
    r = dict(DEFAULTS)
    r.update(overrides)
    return r


def test_defaults_are_valid(schema):
    result = validate_individual(DEFAULTS, schema)
    assert result.is_valid, result.errors
    assert result.warnings == []


def test_defaults_cover_schema_exactly(schema):
    assert set(DEFAULTS) == set(schema["order"])


def test_entry_limits_cover_all_numeric_fields(schema):
    assert set(schema["numeric"]) == set(ENTRY_LIMITS)


def test_missing_required_field(schema):
    r = dict(DEFAULTS)
    del r["BMI"]
    result = validate_individual(r, schema)
    assert "BMI is required." in result.errors


def test_blank_string_is_missing(schema):
    result = validate_individual(rec(Stress="   "), schema)
    assert "Stress is required." in result.errors


def test_non_numeric_rejected(schema):
    result = validate_individual(rec(BMI="abc"), schema)
    assert "BMI must be a number." in result.errors


def test_nan_rejected(schema):
    result = validate_individual(rec(BMI=math.nan), schema)
    assert not result.is_valid


def test_infinity_rejected(schema):
    result = validate_individual(rec(Sleep=math.inf), schema)
    assert not result.is_valid


def test_age_must_be_whole_number(schema):
    result = validate_individual(rec(Age=40.5), schema)
    assert "Age must be a whole number." in result.errors


def test_entry_limits_enforced(schema):
    result = validate_individual(rec(BMI=200), schema)
    assert any(e.startswith("BMI must be between") for e in result.errors)


def test_unexpected_category_rejected(schema):
    result = validate_individual(rec(JunkFood="Sometimes"), schema)
    assert any(e.startswith("JunkFood must be one of") for e in result.errors)


def test_male_with_pregnancies_rejected(schema):
    result = validate_individual(rec(Gender="Male", Pregnancies=2), schema)
    assert "Pregnancies must be 0 when Gender is Male." in result.errors


def test_outside_training_range_is_warning_not_error(schema):
    # BMI 45 is within entry limits but above the training maximum (42).
    result = validate_individual(rec(BMI=45.0), schema)
    assert result.is_valid
    assert any(w.startswith("BMI (45) is outside the range") for w in result.warnings)

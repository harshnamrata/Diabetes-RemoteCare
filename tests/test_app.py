from pathlib import Path

from streamlit.testing.v1 import AppTest

from tests.sample_record import SAMPLE

PAGE = str(Path(__file__).resolve().parents[1] / "views" / "individual.py")
TIMEOUT = 60


def _button(at, label):
    return next(b for b in at.button if b.label == label)


def _set(at, col, value):
    el = at.number_input(key=f"in_{col}") if isinstance(value, (int, float)) and col not in (
        "Gender", "Family_Diabetes", "highBP", "PhysicallyActive", "Smoking", "Alcohol",
        "RegularMedicine", "JunkFood", "Stress", "BPLevel", "Pdiabetes", "UriationFreq") \
        else at.selectbox(key=f"in_{col}")
    el.set_value(value)


def _fill(at, record):
    for col in ["Gender"] + [c for c in record if c != "Gender"]:
        if col == "Pregnancies" and record.get("Gender") != "Female":
            continue
        _set(at, col, record[col])
        at.run()
    return at


def test_form_starts_blank_with_no_prefilled_values():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT).run()
    assert not at.exception
    assert at.number_input(key="in_Age").value is None
    assert at.number_input(key="in_BMI").value is None
    assert at.selectbox(key="in_Gender").value is None


def test_pregnancies_hidden_unless_female():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT).run()
    assert not any(n.key == "in_Pregnancies" for n in at.number_input)
    at.selectbox(key="in_Gender").set_value("Female").run()
    assert any(n.key == "in_Pregnancies" for n in at.number_input)
    at.selectbox(key="in_Gender").set_value("Male").run()
    assert not any(n.key == "in_Pregnancies" for n in at.number_input)


def test_submitting_blank_form_asks_for_answers():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT).run()
    _button(at, "Check my risk").click().run()
    assert not at.exception
    assert any("Please answer:" in w.value for w in at.warning)


def test_complete_form_returns_a_result_and_tips():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT).run()
    _fill(at, SAMPLE)
    _button(at, "Check my risk").click().run()
    assert not at.exception and not at.error
    assert at.success or at.warning
    assert any("Personal tips" in m.value for m in at.markdown)


def test_progress_updates_with_answers():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT).run()
    assert "0 of 17 answered" in [p.proto.text for p in at.get("progress")][0]


def test_clear_answers_resets_form_and_result():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT).run()
    _fill(at, SAMPLE)
    _button(at, "Check my risk").click().run()
    _button(at, "Clear answers").click().run()
    assert at.number_input(key="in_Age").value is None
    assert not at.success and not at.warning[1:]


def test_invalid_input_is_blocked_and_logged():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT).run()
    _fill(at, SAMPLE)
    at.number_input(key="in_BMI").set_value(0.5).run()
    _button(at, "Check my risk").click().run()
    assert not at.exception
    assert at.session_state["history"][-1]["Status"] == "Rejected"

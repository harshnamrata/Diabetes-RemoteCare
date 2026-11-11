from pathlib import Path

from streamlit.testing.v1 import AppTest

PAGE = Path(__file__).resolve().parents[1] / "views" / "individual.py"


def _button(at, label):
    return next(b for b in at.button if b.label == label)


def test_individual_page_renders_without_exceptions():
    at = AppTest.from_file(str(PAGE), default_timeout=60).run()
    assert not at.exception
    assert not at.error
    assert any("Screen patient" == b.label for b in at.button)


def test_submitting_default_form_shows_a_result():
    at = AppTest.from_file(str(PAGE), default_timeout=60).run()
    _button(at, "Screen patient").click().run()
    assert not at.exception
    assert at.success or at.warning
    assert not at.error


def test_invalid_entries_are_blocked_and_explained():
    at = AppTest.from_file(str(PAGE), default_timeout=60).run()
    at.selectbox(key="in_Gender").set_value("Male")
    at.number_input(key="in_Pregnancies").set_value(2)
    _button(at, "Screen patient").click().run()
    assert not at.exception
    assert any("Pregnancies must be 0 when Gender is Male." in m.value for m in at.markdown)
    assert not at.success


def test_reset_restores_defaults_and_clears_result():
    at = AppTest.from_file(str(PAGE), default_timeout=60).run()
    at.number_input(key="in_BMI").set_value(33.0)
    _button(at, "Screen patient").click().run()
    _button(at, "Reset form").click().run()
    assert at.number_input(key="in_BMI").value == 25.0
    assert not at.success

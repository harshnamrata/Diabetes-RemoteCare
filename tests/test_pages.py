from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 60


def _run(path):
    return AppTest.from_file(str(ROOT / path), default_timeout=TIMEOUT).run()


def test_navigation_app_runs_on_overview():
    at = _run("app.py")
    assert not at.exception
    assert not at.error


def test_overview_empty_state_and_metrics():
    # Run through app.py: page_link resolves only for pages registered in st.navigation.
    at = _run("app.py")
    assert not at.exception
    assert any("No screenings yet" in i.value for i in at.info)


def test_model_performance_renders():
    at = _run("views/model_performance.py")
    assert not at.exception and not at.error


def test_reports_history_renders_with_empty_history():
    at = _run("views/reports_history.py")
    assert not at.exception and not at.error
    assert any("No screening operations" in i.value for i in at.info)


def test_about_renders():
    at = _run("views/about.py")
    assert not at.exception and not at.error


def test_individual_screening_logs_one_history_entry_per_submit():
    at = _run("views/individual.py")
    assert not at.exception
    next(b for b in at.button if b.label == "Screen patient").click().run()
    assert not at.exception
    history = at.session_state["history"]
    assert len(history) == 1
    assert history[0]["Mode"] == "Individual screening"
    assert history[0]["Status"] == "Completed"
    assert history[0]["Records scored"] == 1


def test_invalid_individual_submission_logs_rejected_entry():
    at = _run("views/individual.py")
    at.selectbox(key="in_Gender").set_value("Male")
    at.number_input(key="in_Pregnancies").set_value(2)
    next(b for b in at.button if b.label == "Screen patient").click().run()
    history = at.session_state["history"]
    assert history[-1]["Status"] == "Rejected"
    assert history[-1]["Records scored"] == 0


def test_clear_history_resets_state():
    seeded = [{"Timestamp (UTC)": "t", "Mode": "x", "Records received": 1,
               "Records scored": 1, "Records flagged": 0, "Status": "Completed"}]
    at = AppTest.from_file(str(ROOT / "views/reports_history.py"), default_timeout=TIMEOUT)
    at.session_state["history"] = seeded  # seed before the first render so the button is enabled
    at.run()
    assert not at.exception
    next(b for b in at.button if b.label == "Clear session history").click().run()
    assert at.session_state["history"] == []

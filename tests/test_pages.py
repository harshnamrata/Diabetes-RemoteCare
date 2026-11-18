from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 60


def _run(path):
    return AppTest.from_file(str(ROOT / path), default_timeout=TIMEOUT).run()


def test_navigation_has_exactly_five_sidebar_sections():
    at = _run("app.py")
    assert not at.exception and not at.error
    source = (ROOT / "app.py").read_text()
    for title in ["Home", "Individual screening", "Regional screening",
                  "Learn about diabetes", "Reports & history"]:
        assert f'title="{title}"' in source
    for removed in ["Overview", "Model Performance", "About the Project"]:
        assert removed not in source


def test_home_renders_with_model_tab():
    at = _run("app.py")
    assert not at.exception and not at.error


def test_learn_page_renders():
    at = _run("views/learn.py")
    assert not at.exception
    assert any("Get medical help now" in e.value for e in at.error)


def test_history_empty_state():
    at = _run("views/history.py")
    assert not at.exception and not at.error
    assert any("No screenings yet" in i.value for i in at.info)


def test_regional_page_renders_without_upload():
    at = _run("views/regional.py")
    assert not at.exception and not at.error
    assert any("Upload a file" in i.value for i in at.info)


def test_regional_page_has_no_template_or_demo_downloads():
    source = (ROOT / "views" / "regional.py").read_text()
    assert "CSV template" not in source
    assert "demo" not in source.lower()


def test_learn_quiz_scores_perfect_answers():
    from src.learn_content import QUIZ
    at = _run("views/learn.py")
    for i, q in enumerate(QUIZ):
        at.radio(key=f"quiz_{i}").set_value(q["options"][q["answer"]])
    next(b for b in at.button if b.label == "Check my answers").click().run()
    assert not at.exception
    assert any("Perfect score" in s.value for s in at.success)


def test_history_clear_resets_state():
    seeded = [{"Timestamp (UTC)": "2026-11-11T10:00:00+00:00", "Mode": "Individual screening",
               "Records received": 1, "Records scored": 1, "Records flagged": 0,
               "Status": "Completed"}]
    at = AppTest.from_file(str(ROOT / "views/history.py"), default_timeout=TIMEOUT)
    at.session_state["history"] = seeded
    at.run()
    assert not at.exception
    next(b for b in at.button if b.label == "Clear session").click().run()
    assert at.session_state["history"] == []


def test_history_filter_narrows_to_status():
    seeded = [
        {"Timestamp (UTC)": "2026-11-11T10:00:00+00:00", "Mode": "Individual screening",
         "Records received": 1, "Records scored": 1, "Records flagged": 1, "Status": "Completed"},
        {"Timestamp (UTC)": "2026-11-11T11:00:00+00:00", "Mode": "Individual screening",
         "Records received": 1, "Records scored": 0, "Records flagged": 0, "Status": "Rejected"},
    ]
    at = AppTest.from_file(str(ROOT / "views/history.py"), default_timeout=TIMEOUT)
    at.session_state["history"] = seeded
    at.run()
    assert at.metric[0].value == "2"
    at.multiselect[1].set_value(["Completed"]).run()
    assert at.metric[0].value == "1"

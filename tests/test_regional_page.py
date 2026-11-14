from pathlib import Path

from streamlit.testing.v1 import AppTest

PAGE = Path(__file__).resolve().parents[1] / "views" / "regional.py"


def test_regional_page_renders_without_exceptions():
    at = AppTest.from_file(str(PAGE), default_timeout=60).run()
    assert not at.exception
    assert not at.error

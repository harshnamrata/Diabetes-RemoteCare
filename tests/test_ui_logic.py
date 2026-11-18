from datetime import date

import pandas as pd
import pytest

from src.guidance import GENERIC_TIP, personal_tips
from src.history_service import BATCH, INDIVIDUAL, filter_history, make_entry
from src.learn_content import QUIZ, TIPS
from src.regional_aggregation import RANK_OPTIONS, rank_summary


def entry(ts, mode, status, scored=1, flagged=0):
    return make_entry(mode, 1, scored, flagged, status, timestamp=ts)


H = [
    entry("2026-11-10T09:00:00+00:00", INDIVIDUAL, "Completed", 1, 1),
    entry("2026-11-11T09:00:00+00:00", BATCH, "Completed", 380, 150),
    entry("2026-11-12T09:00:00+00:00", INDIVIDUAL, "Rejected", 0, 0),
]


def test_empty_filters_mean_no_filter():
    assert len(filter_history(H, modes=[], statuses=[])) == 3


def test_filter_by_mode_and_status():
    assert len(filter_history(H, modes=[INDIVIDUAL])) == 2
    assert len(filter_history(H, statuses=["Completed"])) == 2
    assert len(filter_history(H, modes=[INDIVIDUAL], statuses=["Completed"])) == 1


def test_filter_by_date_range_is_inclusive():
    out = filter_history(H, start=date(2026, 11, 11), end=date(2026, 11, 11))
    assert len(out) == 1 and out[0]["Mode"] == BATCH


def test_filter_handles_empty_history():
    assert filter_history([], modes=[INDIVIDUAL]) == []


def test_rank_by_count_and_percent_differ():
    summary = pd.DataFrame({
        "Region": ["A", "B"], "Total valid records": [50, 2],
        "Flagged as higher risk": [5, 2], "At-risk %": [10.0, 100.0],
        "Invalid rows excluded": [0, 0], "Small sample": [False, True],
    })
    assert rank_summary(summary, "count").iloc[0]["Region"] == "A"
    assert rank_summary(summary, "percent").iloc[0]["Region"] == "B"
    assert list(rank_summary(summary, "count")["Rank"]) == [1, 2]


def test_rank_rejects_unknown_option():
    with pytest.raises(ValueError):
        rank_summary(pd.DataFrame(), "bogus")


def test_rank_options_are_the_two_documented_choices():
    assert set(RANK_OPTIONS) == {"Flagged count", "At-risk percentage"}


def test_personal_tips_follow_answers():
    tips = personal_tips({"BMI": 31, "PhysicallyActive": "none", "Smoking": "Yes",
                          "JunkFood": "Often", "highBP": "Yes", "Sleep": 4})
    assert any("5%" in t for t in tips)
    assert any("Quitting smoking" in t for t in tips)
    assert tips[-1] == GENERIC_TIP


def test_personal_tips_for_low_risk_answers_only_return_generic():
    assert personal_tips({"BMI": 22, "PhysicallyActive": "one hour or more"}) == [GENERIC_TIP]


def test_personal_tips_are_capped():
    everything = {"BMI": 35, "PhysicallyActive": "none", "Smoking": "Yes", "JunkFood": "Often",
                  "highBP": "Yes", "Family_Diabetes": "Yes", "Stress": "Always",
                  "UriationFreq": "Quite often", "Sleep": 4}
    assert len(personal_tips(everything)) <= 6


def test_quiz_answers_are_valid_options():
    for q in QUIZ:
        assert 0 <= q["answer"] < len(q["options"])
        assert q["explanation"]


def test_tips_are_non_empty():
    assert TIPS and all(isinstance(t, str) and t for t in TIPS)


def test_form_sections_cover_every_model_feature_exactly_once():
    import json
    import re
    from src.config import METADATA_PATH, ROOT
    order = json.loads(METADATA_PATH.read_text())["feature_schema"]["order"]
    source = (ROOT / "views" / "individual.py").read_text()
    block = source[source.index("SECTIONS = ["):source.index("]\n\nst.title")]
    listed = re.findall(r'"([A-Za-z_]+)"', block)
    listed = [c for c in listed if c in order]
    assert sorted(listed) == sorted(order)

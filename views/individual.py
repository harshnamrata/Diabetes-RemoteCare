import streamlit as st

from src.config import DISCLAIMER, ENTRY_LIMITS, FIELD_INFO, WHOLE_NUMBER_FIELDS
from src.guidance import personal_tips
from src.history_service import individual_entry
from src.model_loader import ModelUnavailableError, load_model
from src.prediction_service import screen_individual
from src.ui_state import ensure_state, log_entry

ensure_state()

SECTIONS = [
    ("👤 About you", ["Age", "Gender", "Pregnancies"]),
    ("🩺 Body and blood pressure", ["BMI", "highBP", "BPLevel"]),
    ("🧬 Family and medical history", ["Family_Diabetes", "Pdiabetes", "RegularMedicine"]),
    ("🏃 Daily habits", ["PhysicallyActive", "JunkFood", "Smoking", "Alcohol", "Stress",
                        "Sleep", "SoundSleep", "UriationFreq"]),
]

st.title("🧍 Individual screening")
st.write("Answer each question for the person being screened. Nothing is pre-filled.")

try:
    loaded = load_model()
except ModelUnavailableError as exc:
    st.error(f"The screening model is not available. {exc}")
    st.stop()

schema = loaded.metadata["feature_schema"]
FIELDS = schema["order"]


def clear_answers() -> None:
    for col in FIELDS:
        st.session_state[f"in_{col}"] = None
    st.session_state.pop("last_result", None)


def current_record() -> dict:
    rec = {c: st.session_state.get(f"in_{c}") for c in FIELDS}
    if rec["Gender"] == "Male":
        rec["Pregnancies"] = 0
    return rec


def answered_count(rec: dict) -> int:
    return sum(1 for v in rec.values() if v is not None)


def render_field(col: str) -> None:
    label, help_text = FIELD_INFO[col]
    key = f"in_{col}"
    if col in schema["numeric"]:
        lo, hi = ENTRY_LIMITS[col]
        if col in WHOLE_NUMBER_FIELDS:
            st.number_input(label, min_value=int(lo), max_value=int(hi), value=None, step=1,
                            placeholder="Enter a whole number", key=key, help=help_text)
        else:
            st.number_input(label, min_value=float(lo), max_value=float(hi), value=None,
                            step=0.1, format="%.1f", placeholder="Enter a number", key=key,
                            help=help_text)
    else:
        st.selectbox(label, options=schema["categorical"][col], index=None,
                     placeholder="Choose an option", key=key, help=help_text)


gender = st.session_state.get("in_Gender")
for title, cols in SECTIONS:
    visible = [c for c in cols if not (c == "Pregnancies" and gender != "Female")]
    with st.container(border=True):
        st.markdown(f"#### {title}")
        for i in range(0, len(visible), 2):
            pair = st.columns(2)
            for j, col in enumerate(visible[i:i + 2]):
                with pair[j]:
                    render_field(col)

rec_now = current_record()
done = answered_count(rec_now)
st.progress(done / len(FIELDS), text=f"{done} of {len(FIELDS)} answered")

b1, b2 = st.columns([3, 1])
check = b1.button("Check my risk", type="primary", width="stretch")
b2.button("Clear answers", on_click=clear_answers, width="stretch")

if check:
    with st.spinner("Checking..."):
        result = screen_individual(rec_now)
    st.session_state["last_result"] = result
    log_entry(individual_entry(result.status, result.flagged))

result = st.session_state.get("last_result")
if result is not None:
    st.divider()
    if result.status == "invalid":
        missing = [FIELD_INFO[e.split(" is required.")[0]][0]
                   for e in result.errors if e.endswith(" is required.")]
        other = [e for e in result.errors if not e.endswith(" is required.")]
        if missing:
            st.warning("Please answer: " + ", ".join(missing))
        for e in other:
            st.error(e)
    elif result.status in ("unavailable", "error"):
        st.error(result.message)
    else:
        if result.flagged:
            st.warning("### ⚠️ Worth a check-up")
            st.write("This person's answers match patterns linked to higher risk. "
                     "Arrange a blood sugar test with a clinician.")
        else:
            st.success("### ✅ Lower risk for now")
            st.write("This does not rule out diabetes. Keep healthy habits and re-check if "
                     "anything changes.")
        st.progress(float(result.probability), text=f"Estimated risk score: {result.probability:.0%}")
        st.markdown("**Personal tips**")
        for tip in personal_tips(rec_now):
            st.markdown(f"- {tip}")
        st.caption("Counted in this session's report. No answers are stored.")
        for w in result.warnings:
            st.info(w)

st.caption(DISCLAIMER)

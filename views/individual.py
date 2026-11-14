"""Individual screening (Stage 4), with session history logging."""
import streamlit as st

from src.config import DEFAULTS, DISCLAIMER, ENTRY_LIMITS, FIELD_INFO, MODEL_NOTICE
from src.history_service import individual_entry
from src.model_loader import ModelUnavailableError, load_model
from src.prediction_service import screen_individual
from src.ui_state import ensure_state, log_entry

ensure_state()
WHOLE = {"Age", "Pregnancies"}

st.title("Individual Diabetes-Risk Screening")
st.caption("RemoteCare AI · screening aid for frontline use")
st.warning(MODEL_NOTICE)

try:
    loaded = load_model()
except ModelUnavailableError as exc:
    st.error(f"The screening model is not available. {exc}")
    st.stop()

schema = loaded.metadata["feature_schema"]


def reset_form() -> None:
    for col in schema["order"]:
        st.session_state[f"in_{col}"] = DEFAULTS[col]
    st.session_state.pop("last_result", None)


for col in schema["order"]:
    st.session_state.setdefault(f"in_{col}", DEFAULTS[col])


def render_field(col: str) -> None:
    label, help_text = FIELD_INFO[col]
    key = f"in_{col}"
    if col in schema["numeric"]:
        lo, hi = ENTRY_LIMITS[col]
        if col in WHOLE:
            st.number_input(label, min_value=int(lo), max_value=int(hi), step=1, key=key, help=help_text)
        else:
            st.number_input(label, min_value=float(lo), max_value=float(hi), step=0.1,
                            format="%.1f", key=key, help=help_text)
    else:
        st.selectbox(label, options=schema["categorical"][col], key=key, help=help_text)


with st.form("screening_form"):
    st.subheader("Patient details")
    left, right = st.columns(2)
    for i, col in enumerate(schema["order"]):
        with (left if i % 2 == 0 else right):
            render_field(col)
    submit_col, reset_col = st.columns(2)
    with submit_col:
        submitted = st.form_submit_button("Screen patient", type="primary", width="stretch")
    with reset_col:
        st.form_submit_button("Reset form", on_click=reset_form, width="stretch")

if submitted:
    record = {col: st.session_state[f"in_{col}"] for col in schema["order"]}
    with st.spinner("Running the screening model..."):
        result = screen_individual(record)
    st.session_state["last_result"] = result
    log_entry(individual_entry(result.status, result.flagged))


def render_result(r) -> None:
    st.divider()
    st.subheader("Screening result")
    if r.status == "invalid":
        st.error("Please correct the following before screening:")
        for e in r.errors:
            st.markdown(f"- {e}")
    elif r.status in ("unavailable", "error"):
        st.error(r.message)
    else:
        if r.flagged:
            st.warning(
                "**Flagged for further assessment.** The entries match the pattern of higher-risk "
                "records in the training data. Please arrange appropriate clinical assessment and "
                "diagnostic testing.")
        else:
            st.success(
                "**Not flagged by the screening model.** This does not rule out diabetes. "
                "Seek clinical advice if symptoms or concerns remain.")
        st.metric("Estimated model probability", f"{r.probability:.0%}")
        st.caption(
            "This is a model-generated estimate from synthetic training data. It is not a "
            f"calibrated estimate of this person's actual risk. Flag threshold: {r.threshold:.0%}.")
    for w in r.warnings:
        st.info(w)
    st.caption(DISCLAIMER)


result = st.session_state.get("last_result")
if result is not None:
    render_result(result)

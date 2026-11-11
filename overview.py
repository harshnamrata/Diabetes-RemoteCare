"""Overview dashboard: every figure comes from the saved model or this session's actual activity."""
import streamlit as st

from src.config import DISCLAIMER, MODEL_NOTICE
from src.history_service import session_totals
from src.model_loader import ModelUnavailableError, load_evaluation, load_model
from src.ui_state import HISTORY, LAST_BATCH, ensure_state

ensure_state()

st.title("RemoteCare AI")
st.subheader("Early screening of diabetes in remote areas")
st.write("A machine-learning screening aid for frontline health workers. It flags individuals "
         "who may need further assessment and helps prioritise regional follow-up. It is not a "
         "diagnostic tool.")
st.warning(MODEL_NOTICE)

try:
    loaded = load_model()
    evaluation = load_evaluation()
except ModelUnavailableError as exc:
    st.error(f"The screening model is not available. {exc}")
    st.stop()

md = loaded.metadata
selected = evaluation["selected_model"]
test = evaluation["test_set_results"][selected]

st.subheader("Get started")
n1, n2, n3 = st.columns(3)
n1.page_link("views/individual.py", label="Screen an individual", icon="🧍")
n2.page_link("views/regional.py", label="Screen a regional file", icon="🗺️")
n3.page_link("views/reports_history.py", label="Reports and history", icon="📄")

st.subheader("This session")
totals = session_totals(st.session_state[HISTORY])
if totals["operations"] == 0:
    st.info("No screenings yet this session. Results appear here as you screen individuals or "
            "upload regional files.")
m1, m2, m3 = st.columns(3)
m1.metric("Screening operations", f"{totals['operations']:,}")
m2.metric("Records scored", f"{totals['records_scored']:,}")
m3.metric("Records flagged as higher risk", f"{totals['records_flagged']:,}")

st.subheader("Regional summary (latest batch)")
snap = st.session_state[LAST_BATCH]
if snap is None:
    st.info("No regional batch has been processed this session.")
else:
    s = snap["summary"]
    top = s.iloc[0]
    r1, r2, r3 = st.columns(3)
    r1.metric("Regional records scored", f"{snap['scored']:,}")
    r2.metric("Regions processed", f"{len(s):,}")
    r3.metric("Highest-ranked region", str(top["Region"]),
              help="Ranked by the sort option chosen on the Regional Screening page.")
    st.caption(f"Top region: {top['Flagged as higher risk']} flagged of "
               f"{top['Total valid records']} valid records"
               + (f" ({top['At-risk %']:.1f}%)." if top["Total valid records"] else "."))

st.subheader("Model")
st.table({
    "Item": ["Selected model", "Model version", "Trained (UTC)",
             "Training data", "Test recall (positive class)",
             "Test precision", "Test ROC-AUC"],
    "Value": [selected, md["model_version"], md["trained_at_utc"],
              f"Synthetic, {md['dataset']['rows']:,} rows",
              f"{test['recall']:.3f}", f"{test['precision']:.3f}", f"{test['roc_auc']:.3f}"],
})
st.caption("Metrics are from synthetic data and do not describe real populations. "
           "See Model Performance for details.")
st.caption(DISCLAIMER)

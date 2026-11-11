"""Session history and downloadable report. Session-only: nothing is stored after the session."""
from datetime import datetime, timezone

import streamlit as st

from src.config import MODEL_NOTICE
from src.export_safety import to_safe_csv_bytes
from src.history_service import history_frame
from src.model_loader import ModelUnavailableError, load_evaluation, load_model
from src.report_generator import build_markdown_report
from src.ui_state import HISTORY, LAST_BATCH, clear_session, ensure_state

ensure_state()
st.title("Reports and History")
st.warning(MODEL_NOTICE)

st.info(
    "**Session-only.** History and reports live in this browser session and are cleared when it "
    "ends. Nothing here is saved to a database or disk. Persistent history would need access "
    "controls and a retention policy, which this prototype does not implement.")

st.subheader("Session history")
history = st.session_state[HISTORY]
if not history:
    st.info("No screening operations recorded yet this session.")
else:
    st.dataframe(history_frame(history), hide_index=True, width="stretch")
    st.caption("History holds counts and status only: no names, IDs, or feature values.")

h1, h2 = st.columns(2)
with h1:
    st.download_button("Download history (CSV)",
                       to_safe_csv_bytes(history_frame(history)),
                       "session_history.csv", "text/csv", disabled=not history)
with h2:
    st.button("Clear session history", on_click=clear_session, disabled=not history,
              help="Clears history and the latest regional summary for this session.")

st.subheader("Session report")
try:
    loaded = load_model()
    evaluation = load_evaluation()
except ModelUnavailableError as exc:
    st.error(f"The report cannot be generated. {exc}")
    st.stop()

generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
report = build_markdown_report(loaded.metadata, evaluation, history,
                               st.session_state[LAST_BATCH], generated)
st.download_button("Download session report (Markdown)", report.encode(),
                   "remotecare_session_report.md", "text/markdown")
st.caption("The report includes model and dataset facts, the evaluation summary, this session's "
           "history, and the latest regional ranking. It contains no patient-level records.")
with st.expander("Preview report"):
    st.markdown(report)

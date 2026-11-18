from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from src.config import DISCLAIMER
from src.export_safety import to_safe_csv_bytes
from src.history_service import BATCH, INDIVIDUAL, filter_history, history_frame, session_totals
from src.model_loader import ModelUnavailableError, load_evaluation, load_model
from src.report_generator import build_markdown_report
from src.ui_state import HISTORY, LAST_BATCH, clear_session, ensure_state

ensure_state()

st.title("📄 Reports & history")
st.write("Everything in this session, filtered however you like. Session-only: it is cleared when "
         "the session ends.")

history = st.session_state[HISTORY]

if not history:
    st.info("No screenings yet this session. Screen someone and their entry will appear here.")
else:
    days = [datetime.fromisoformat(e["Timestamp (UTC)"]).date() for e in history]
    lo, hi = min(days), max(days)

    with st.container(border=True):
        st.markdown("#### 🔎 Filters")
        f1, f2, f3 = st.columns(3)
        modes = f1.multiselect("Screening type", [INDIVIDUAL, BATCH], default=[INDIVIDUAL, BATCH])
        statuses = f2.multiselect("Status", ["Completed", "Rejected", "Error"],
                                  default=["Completed", "Rejected", "Error"])
        rng = f3.date_input("Date range", value=(lo, hi), min_value=lo, max_value=hi)
        st.caption("Clear a filter to show all of its values.")

    start, end = (rng[0], rng[1]) if isinstance(rng, (tuple, list)) and len(rng) == 2 else (lo, hi)
    filtered = filter_history(history, modes=modes, statuses=statuses, start=start, end=end)
    totals = session_totals(filtered)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Operations shown", f"{len(filtered):,}")
    k2.metric("Completed", f"{totals['completed']:,}")
    k3.metric("Records screened", f"{totals['records_scored']:,}")
    k4.metric("Flagged for check-up", f"{totals['records_flagged']:,}")

    if filtered:
        left, right = st.columns([3, 2])
        with left:
            st.dataframe(history_frame(filtered), hide_index=True, width="stretch")
        with right:
            by_mode = (pd.DataFrame(filtered)
                       .query("Status == 'Completed'")
                       .groupby("Mode")["Records scored"].sum())
            if not by_mode.empty:
                st.markdown("**Records screened by type**")
                st.bar_chart(by_mode)
    else:
        st.warning("No entries match these filters.")

    d1, d2, d3 = st.columns(3)
    d1.download_button("Download filtered history (CSV)",
                       to_safe_csv_bytes(history_frame(filtered)), "session_history.csv",
                       "text/csv", disabled=not filtered, width="stretch")
    st.button("Clear session", on_click=clear_session, width="stretch")

st.divider()
st.markdown("#### 📑 Session report")
try:
    loaded = load_model()
    evaluation = load_evaluation()
except ModelUnavailableError as exc:
    st.error(f"The report cannot be generated. {exc}")
    st.stop()

generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
report = build_markdown_report(loaded.metadata, evaluation, history,
                               st.session_state[LAST_BATCH], generated)
st.write("The full report covers model details, evaluation, every entry in this session "
         "(not just the filtered view), and the latest regional ranking.")
st.download_button("Download session report (Markdown)", report.encode(),
                   "remotecare_session_report.md", "text/markdown")
with st.expander("Preview"):
    st.markdown(report)

st.caption(DISCLAIMER)

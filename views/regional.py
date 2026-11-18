import streamlit as st

from src.batch_processing import MAX_ROWS, MAX_UPLOAD_BYTES, process_batch
from src.config import DISCLAIMER
from src.export_safety import to_safe_csv_bytes
from src.history_service import batch_entry, batch_snapshot, should_log_batch, upload_fingerprint
from src.model_loader import ModelUnavailableError, load_model
from src.regional_aggregation import RANK_OPTIONS, rank_summary
from src.ui_state import BATCH_FINGERPRINT, LAST_BATCH, ensure_state, log_entry

ensure_state()

st.title("🗺️ Regional screening")
st.write("Upload a CSV of records tagged by region. Each valid record is screened, then areas "
         "are ranked by the number of people flagged.")

try:
    loaded = load_model()
except ModelUnavailableError as exc:
    st.error(f"The screening model is not available. {exc}")
    st.stop()

with st.expander("📋 What the file needs"):
    st.markdown(
        "- A **Region** column, then the 17 screening questions, named exactly as in the "
        "Individual screening form.\n"
        "- Extra columns are ignored. Rows with errors are listed, never silently dropped.\n"
        "- Exact duplicate rows are counted once.\n"
        f"- Limits: {MAX_UPLOAD_BYTES // (1024 * 1024)} MB and {MAX_ROWS:,} rows.")

uploaded = st.file_uploader("Upload a regional CSV", type=["csv"])

if uploaded is None:
    st.info("Upload a file to begin. It is processed in memory and not stored.")
    st.stop()

data = uploaded.getvalue()
with st.spinner("Screening records..."):
    result = process_batch(data, uploaded.name)

fingerprint = upload_fingerprint(data)
if should_log_batch(st.session_state[BATCH_FINGERPRINT], fingerprint):
    st.session_state[BATCH_FINGERPRINT] = fingerprint
    log_entry(batch_entry(result))
if result.status == "ok":
    st.session_state[LAST_BATCH] = batch_snapshot(result)

if result.status != "ok":
    st.error(result.message)
    st.stop()

st.success(result.message)
m1, m2, m3 = st.columns(3)
m1.metric("Records screened", f"{result.valid_rows:,}")
m2.metric("Flagged for check-up", f"{result.flagged_rows:,}")
m3.metric("Regions", f"{len(result.summary):,}")

if not result.issues.empty:
    n_warn = int((result.issues["Severity"] == "Warning").sum())
    st.warning(f"{result.excluded_rows} row(s) excluded and {n_warn} warning(s). See the details below.")
    with st.expander(f"⚠️ Row issues ({len(result.issues)})", expanded=result.excluded_rows > 0):
        st.dataframe(result.issues, hide_index=True, width="stretch")

if result.valid_rows == 0:
    st.warning("No valid records were available to screen.")
    st.stop()

st.subheader("Ranking")
choice = st.radio("Rank regions by", list(RANK_OPTIONS), index=None, horizontal=True,
                  key="rank_by", help="Choose a ranking to show the table and charts.")

if choice is None:
    st.info("👆 Choose how to rank the regions to see the table and charts.")
else:
    ranked = rank_summary(result.summary, RANK_OPTIONS[choice])
    st.caption("**Count**: records flagged by the model. **Percentage**: flagged ÷ valid records "
               "in that region. Small regions (fewer than 30 records) are marked.")
    st.dataframe(ranked, hide_index=True, width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Flagged count by region**")
        st.bar_chart(ranked.set_index("Region")["Flagged as higher risk"])
    with c2:
        st.markdown("**At-risk percentage by region**")
        st.bar_chart(ranked.set_index("Region")["At-risk %"].fillna(0))

    processed = result.results.copy()
    processed["Probability"] = processed["Probability"].round(3)
    processed["Flagged"] = processed["Flagged"].map({True: "Yes", False: "No"})
    d1, d2 = st.columns(2)
    d1.download_button("Download ranking (CSV)", to_safe_csv_bytes(ranked),
                       "regional_ranking.csv", "text/csv", width="stretch")
    d2.download_button("Download screening results (CSV)", to_safe_csv_bytes(processed),
                       "screening_results.csv", "text/csv", width="stretch")
    st.caption("Results contain row number, region, probability and flag only. No health values.")

st.caption(DISCLAIMER)

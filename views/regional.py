"""Regional batch screening (Stage 5), with session history and dashboard snapshot."""
import pandas as pd
import streamlit as st

from src.export_safety import to_safe_csv_bytes
from src.batch_processing import MAX_ROWS, MAX_UPLOAD_BYTES, process_batch
from src.config import DISCLAIMER, MODEL_NOTICE, ROOT
from src.history_service import batch_entry, batch_snapshot, should_log_batch, upload_fingerprint
from src.model_loader import ModelUnavailableError, load_model
from src.ui_state import BATCH_FINGERPRINT, LAST_BATCH, ensure_state, log_entry

ensure_state()
DEMO_PATH = ROOT / "data" / "sample" / "SYNTHETIC_regional_demo.csv"

st.title("Regional Batch Screening")
st.caption("Upload a CSV of records tagged by region. Each valid record is scored by the same "
           "model used for individual screening.")
st.warning(MODEL_NOTICE)
st.info("Regional data in this prototype are synthetic demonstration records. Counts describe "
        "records the model flagged. They are not population prevalence.")

try:
    loaded = load_model()
except ModelUnavailableError as exc:
    st.error(f"The screening model is not available. {exc}")
    st.stop()

schema = loaded.metadata["feature_schema"]
template_bytes = pd.DataFrame(columns=["Region"] + schema["order"]).to_csv(index=False).encode()

c1, c2 = st.columns(2)
c1.download_button("Download CSV template", template_bytes,
                   "remotecare_batch_template.csv", "text/csv")
if DEMO_PATH.exists():
    c2.download_button("Download synthetic demo file", DEMO_PATH.read_bytes(),
                       DEMO_PATH.name, "text/csv")

with st.expander("Required columns and rules"):
    st.markdown(
        "- **Region** (required, up to 64 characters) plus the 17 model features, "
        "named exactly as in the template.\n"
        "- Extra columns are ignored. Rows with errors are excluded and listed, never silently dropped.\n"
        "- Exact duplicate rows are excluded after their first occurrence.\n"
        f"- Limits: {MAX_UPLOAD_BYTES // (1024 * 1024)} MB and {MAX_ROWS:,} rows.")

uploaded = st.file_uploader("Upload regional CSV", type=["csv"])
sort_choice = st.radio("Rank regions by", ["Flagged count", "At-risk percentage"], horizontal=True)

if uploaded is None:
    st.info("Upload a CSV to begin. Uploaded data are processed in memory for this session only.")
    st.stop()

data = uploaded.getvalue()
with st.spinner("Validating and scoring records..."):
    result = process_batch(data, uploaded.name,
                           sort_by="percent" if sort_choice == "At-risk percentage" else "count")

# Log each distinct upload once, not on every rerun.
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
m1.metric("Valid records scored", f"{result.valid_rows:,}")
m2.metric("Flagged as higher risk", f"{result.flagged_rows:,}")
m3.metric("Regions processed", f"{len(result.summary):,}")

if result.issues.empty:
    st.caption("No validation issues found.")
else:
    n_excluded = int((result.issues["Severity"] == "Excluded").sum())
    n_warn = int((result.issues["Severity"] == "Warning").sum())
    st.warning(f"{result.excluded_rows} row(s) excluded; {n_warn} warning(s) on scored rows. "
               "Details below.")
    with st.expander(f"Validation issues ({len(result.issues)})", expanded=n_excluded > 0):
        st.dataframe(result.issues, hide_index=True, width="stretch")

if result.valid_rows == 0:
    st.warning("No valid records were available to score.")
    st.stop()

st.subheader("Regional ranking")
st.caption("**Count** is the number of records the model flagged. **Percentage** is flagged "
           "divided by valid records in that region. A small region can show a high percentage "
           "with a low count; see the Small sample column.")
st.dataframe(result.summary, hide_index=True, width="stretch")

ch1, ch2 = st.columns(2)
with ch1:
    st.markdown("**Flagged records by region**")
    st.bar_chart(result.summary.set_index("Region")["Flagged as higher risk"])
with ch2:
    st.markdown("**At-risk percentage by region**")
    st.caption("Regions with no valid records show 0 here.")
    st.bar_chart(result.summary.set_index("Region")["At-risk %"].fillna(0))

st.subheader("Downloads")
d1, d2 = st.columns(2)
d1.download_button("Download regional summary (CSV)",
                   to_safe_csv_bytes(result.summary), "regional_summary.csv", "text/csv")
processed = result.results.copy()
processed["Probability"] = processed["Probability"].round(3)
processed["Flagged"] = processed["Flagged"].map({True: "Yes", False: "No"})
d2.download_button("Download processed results (CSV)",
                   to_safe_csv_bytes(processed), "processed_results.csv", "text/csv")
st.caption("Processed results contain row number, region, probability and flag only. "
           "They contain no health values.")
st.caption(DISCLAIMER)

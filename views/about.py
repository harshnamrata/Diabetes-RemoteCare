"""About the project: scope, data, safety, privacy and limitations."""
import streamlit as st

from src.config import DISCLAIMER, MODEL_NOTICE, ROOT
from src.ui_state import ensure_state

ensure_state()
st.title("About the Project")
st.warning(MODEL_NOTICE)

st.subheader("Purpose")
st.write("RemoteCare AI is a minor-project prototype. It explores whether a simple ML classifier, "
         "used through a two-mode screening tool, can help frontline workers prioritise diabetes "
         "assessment in areas with limited access to screening. The same model powers individual "
         "and regional screening.")

st.subheader("Data")
st.write("The model is trained on a synthetic dataset that follows the expected Diabetes Dataset "
         "2019 schema. Column names are unverified against the real dataset. Regional demo records "
         "are also synthetic and use placeholder region names.")

st.subheader("Safety and privacy")
st.markdown(
    "- The tool supports screening decisions. It does not diagnose diabetes.\n"
    "- Results are estimates and are not calibrated to any individual's risk.\n"
    "- No personal identifiers are collected. The app never writes uploaded files to disk, but Streamlit's upload handling may buffer them temporarily.\n"
    "- Session history holds counts only and is cleared when the session ends.\n"
    "- Log lines never record patient values.")

st.subheader("Known limitations")
st.markdown(
    "- Not clinically validated, and metrics come from synthetic data.\n"
    "- No login or role-based access: single-user local prototype, accepted for this project.\n"
    "- The 0.5 threshold with balanced class weights flags more records than the training base rate.\n"
    "- Saved model files are pickle-based; load only trusted artifacts.\n"
    "- Not ready for real healthcare deployment without validation, governance and legal review.")

with st.expander("Model card"):
    card = ROOT / "docs" / "model_card.md"
    if card.exists():
        st.markdown(card.read_text())
    else:
        st.info("Model card not found.")

st.caption(DISCLAIMER)

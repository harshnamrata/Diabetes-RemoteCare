import datetime as dt

import streamlit as st

from src.config import DISCLAIMER, ROOT
from src.learn_content import TIPS
from src.model_loader import ModelUnavailableError, load_evaluation

ASSETS = ROOT / "assets"

left, right = st.columns([3, 2], vertical_alignment="center")
with left:
    st.markdown('<div class="rc-hero">', unsafe_allow_html=True)
    st.title("RemoteCare AI")
    st.subheader("Early diabetes screening for remote communities")
    st.write("Check someone's risk in a few minutes, get simple next steps, and learn how to "
             "protect your blood sugar.")
    b1, b2 = st.columns(2)
    b1.page_link("views/individual.py", label="Screen a person", icon="🧍", width="stretch")
    b2.page_link("views/regional.py", label="Screen a region", icon="🗺️", width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)
with right:
    st.image(str(ASSETS / "hero.png"))

st.write("")
s1, s2, s3 = st.columns(3)
with s1.container(border=True):
    st.markdown('<div class="rc-step">Step 1</div>', unsafe_allow_html=True)
    st.markdown("**Answer the questions**")
    st.caption("Enter the person's details. Nothing is pre-filled.")
with s2.container(border=True):
    st.markdown('<div class="rc-step">Step 2</div>', unsafe_allow_html=True)
    st.markdown("**See the result**")
    st.caption("A risk flag, an estimated score and personal tips.")
with s3.container(border=True):
    st.markdown('<div class="rc-step">Step 3</div>', unsafe_allow_html=True)
    st.markdown("**Act early**")
    st.caption("Book a blood sugar test with a clinician if flagged.")

st.write("")
m1, m2, m3 = st.columns(3)
m1.metric("People living with diabetes", "830 million", help="WHO estimate for 2022.")
m2.metric("Activity goal", "150 min / week", help="Moderate activity for adults.")
m3.metric("Early diabetes", "Often silent", help="Many people feel well for years.")

day_tip = TIPS[dt.date.today().toordinal() % len(TIPS)]
st.markdown(f'<div class="rc-tip"><b>💡 Tip of the day:</b> {day_tip}</div>', unsafe_allow_html=True)

tab_how, tab_model, tab_about = st.tabs(["How it works", "Model at a glance", "About this project"])
with tab_how:
    st.write("RemoteCare AI uses one machine-learning model for two jobs. Individual screening "
             "checks one person. Regional screening checks a whole CSV of records and ranks "
             "areas by how many people were flagged.")
    st.write("The model estimates risk from health and lifestyle answers. It is a screening "
             "prompt that tells you who needs a proper test. It cannot diagnose diabetes.")
with tab_model:
    try:
        ev = load_evaluation()
        sel = ev["selected_model"]
        t = ev["test_set_results"][sel]
        c1, c2, c3 = st.columns(3)
        c1.metric("Selected model", sel)
        c2.metric("Recall (held-out)", f"{t['recall']:.0%}", help="Share of positive cases the model flagged.")
        c3.metric("ROC-AUC (held-out)", f"{t['roc_auc']:.2f}")
        st.caption("Measured on synthetic training data. Results will differ on real patients.")
        st.dataframe(
            {"Model": list(ev["test_set_results"]),
             "Recall": [round(r["recall"], 3) for r in ev["test_set_results"].values()],
             "Precision": [round(r["precision"], 3) for r in ev["test_set_results"].values()],
             "ROC-AUC": [round(r["roc_auc"], 3) for r in ev["test_set_results"].values()]},
            hide_index=True, width="stretch")
    except ModelUnavailableError as exc:
        st.error(str(exc))
with tab_about:
    st.write("A minor-project prototype for remote and under-resourced communities. It is built "
             "with Python, Streamlit and scikit-learn, and currently uses synthetic data.")
    st.write("No names or identifiers are collected. Session history keeps counts only and is "
             "cleared when the session ends.")

st.caption(DISCLAIMER)

import streamlit as st

from src.config import DISCLAIMER, ROOT
from src.learn_content import (BASICS, GET_HELP_NOW, PRECAUTIONS, PREVENTION, QUIZ,
                               TYPES, WARNING_SIGNS)

ASSETS = ROOT / "assets"

st.title("📘 Learn about diabetes")
st.write("Short, practical facts. Use them to start a conversation with a clinician.")

tab_basics, tab_signs, tab_prevent, tab_care, tab_quiz = st.tabs(
    ["The basics", "Warning signs", "Prevention", "Precautions", "Quiz"])

with tab_basics:
    left, right = st.columns([3, 2], vertical_alignment="center")
    with left:
        for line in BASICS:
            st.markdown(f"- {line}")
    with right:
        st.image(str(ASSETS / "bmi_scale.png"))
    st.markdown("#### Types of diabetes")
    cols = st.columns(2)
    for i, (name, text) in enumerate(TYPES):
        with cols[i % 2].container(border=True):
            st.markdown(f"**{name}**")
            st.write(text)

with tab_signs:
    st.image(str(ASSETS / "warning_signs.png"))
    st.markdown("#### Watch for")
    for s in WARNING_SIGNS:
        st.markdown(f"- {s}")
    st.info("Many people have no symptoms at all. A simple blood test is the only way to know.")

with tab_prevent:
    left, right = st.columns([2, 3], vertical_alignment="center")
    with left:
        st.image(str(ASSETS / "healthy_plate.png"))
    with right:
        for p in PREVENTION:
            st.markdown(f"- {p}")
    st.image(str(ASSETS / "activity.png"))

with tab_care:
    st.markdown("#### Everyday precautions")
    for p in PRECAUTIONS:
        st.markdown(f"- {p}")
    st.error("**Get medical help now if:**\n\n" + "\n".join(f"- {g}" for g in GET_HELP_NOW))

with tab_quiz:
    st.write("Five quick questions. Answer all of them, then check your score.")
    with st.form("quiz"):
        picks = []
        for i, q in enumerate(QUIZ):
            picks.append(st.radio(f"{i + 1}. {q['question']}", q["options"], index=None,
                                  key=f"quiz_{i}"))
        submitted = st.form_submit_button("Check my answers", type="primary")
    if submitted:
        if any(p is None for p in picks):
            st.warning("Please answer every question first.")
        else:
            score = 0
            for i, (q, pick) in enumerate(zip(QUIZ, picks)):
                if q["options"].index(pick) == q["answer"]:
                    score += 1
                    st.success(f"**{i + 1}.** Correct. {q['explanation']}")
                else:
                    st.error(f"**{i + 1}.** Not quite. {q['explanation']}")
            if score == len(QUIZ):
                st.balloons()
                st.success(f"🎉 Perfect score: {score} of {len(QUIZ)}. Well done!")
            elif score >= 3:
                st.info(f"👏 Good work: {score} of {len(QUIZ)}.")
            else:
                st.info(f"📚 You got {score} of {len(QUIZ)}. Read the other tabs and try again.")

st.caption(DISCLAIMER)

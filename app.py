import streamlit as st

from src.history_service import session_totals
from src.ui_state import HISTORY, ensure_state
from src.ui_theme import apply_theme

st.set_page_config(page_title="RemoteCare AI", page_icon="🩺", layout="wide")
ensure_state()
apply_theme()

pages = [
    st.Page("views/home.py", title="Home", icon="🏠", default=True),
    st.Page("views/individual.py", title="Individual screening", icon="🧍"),
    st.Page("views/regional.py", title="Regional screening", icon="🗺️"),
    st.Page("views/learn.py", title="Learn about diabetes", icon="📘"),
    st.Page("views/history.py", title="Reports & history", icon="📄"),
]

with st.sidebar:
    totals = session_totals(st.session_state[HISTORY])
    st.metric("Screenings this session", totals["operations"])
    st.caption("Prototype on synthetic data. Not a diagnosis.")

st.navigation(pages).run()

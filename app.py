"""RemoteCare AI entry point. Navigation between the six sections."""
import streamlit as st

from src.ui_state import ensure_state

st.set_page_config(page_title="RemoteCare AI", page_icon="🩺", layout="wide")
ensure_state()

pages = [
    st.Page("views/overview.py", title="Overview", icon="🏠", default=True),
    st.Page("views/individual.py", title="Individual Screening", icon="🧍"),
    st.Page("views/regional.py", title="Regional Screening", icon="🗺️"),
    st.Page("views/model_performance.py", title="Model Performance", icon="📊"),
    st.Page("views/reports_history.py", title="Reports and History", icon="📄"),
    st.Page("views/about.py", title="About the Project", icon="ℹ️"),
]
st.navigation(pages).run()

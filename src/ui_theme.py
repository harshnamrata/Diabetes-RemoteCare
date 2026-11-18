import streamlit as st

CSS = """
<style>
.block-container { padding-top: 1.5rem; max-width: 1200px; }
h1, h2, h3 { color: #0f172a; }
.rc-hero { background: linear-gradient(135deg, #ecfeff 0%, #eff6ff 100%);
  border: 1px solid #cffafe; border-radius: 18px; padding: 1.6rem 1.8rem; }
.rc-tip { background: #f0fdfa; border-left: 4px solid #0f766e; border-radius: 10px;
  padding: .75rem 1rem; color: #134e4a; }
.rc-step { color: #0f766e; font-weight: 700; font-size: .8rem; letter-spacing: .06em;
  text-transform: uppercase; }
.rc-badge { display: inline-block; padding: .2rem .65rem; border-radius: 999px;
  background: #e0f2fe; color: #075985; font-size: .8rem; font-weight: 600; margin-right: .35rem; }
[data-testid="stSidebar"] { background: #f8fafc; }
</style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

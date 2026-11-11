"""Streamlit session-state keys and helpers. Session-only; cleared when the browser session ends."""
import streamlit as st

from src.history_service import append_entry

HISTORY = "history"
LAST_BATCH = "last_batch"
BATCH_FINGERPRINT = "batch_fingerprint"


def ensure_state() -> None:
    st.session_state.setdefault(HISTORY, [])
    st.session_state.setdefault(LAST_BATCH, None)
    st.session_state.setdefault(BATCH_FINGERPRINT, None)


def log_entry(entry: dict | None) -> None:
    st.session_state[HISTORY] = append_entry(st.session_state[HISTORY], entry)


def clear_session() -> None:
    st.session_state[HISTORY] = []
    st.session_state[LAST_BATCH] = None
    st.session_state[BATCH_FINGERPRINT] = None

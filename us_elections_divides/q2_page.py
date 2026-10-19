from __future__ import annotations

import streamlit as st

from src import ui, views
from src.load import get

states = get("state_results")

with st.container(key="state_shift"):
    views.render_state_shift(states)

st.page_link("q3_page.py", label="Next question →")

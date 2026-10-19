from __future__ import annotations

import streamlit as st

from src import ui, views
from src.load import get

shift = get("state_search_shift")

with st.container(key="search_by_state"):
    views.render_search_by_state(shift)

st.page_link("about_page.py", label="About the data →")

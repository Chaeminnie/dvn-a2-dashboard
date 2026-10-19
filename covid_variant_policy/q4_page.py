from __future__ import annotations

import streamlit as st

from src import views
from src.load import get_panel, get_summary

summary = get_summary()

with st.container(key="outcomes_by_timing"):
    views.render_outcomes_by_timing(summary)

st.page_link("about_page.py", label="About the data →")

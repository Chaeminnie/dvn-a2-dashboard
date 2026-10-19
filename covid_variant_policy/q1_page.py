from __future__ import annotations

import streamlit as st

from src import views
from src.load import get_panel, get_summary

panel = get_panel()
summary = get_summary()

with st.container(key="who_moved_first"):
    views.render_who_moved_first(summary, panel)

st.page_link("q2_page.py", label="Next question →")

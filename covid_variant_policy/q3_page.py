from __future__ import annotations

import streamlit as st

from src import views
from src.load import get_panel, get_summary

panel = get_panel()

with st.container(key="people_vs_rules"):
    views.render_people_vs_rules(panel)

st.page_link("q4_page.py", label="Next question →")

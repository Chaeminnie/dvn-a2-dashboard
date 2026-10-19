from __future__ import annotations

import streamlit as st

from src import views
from src.load import get_panel, get_summary

summary = get_summary()

with st.container(key="response_differs"):
    views.render_response_differs(summary)

st.page_link("q3_page.py", label="Next question →")

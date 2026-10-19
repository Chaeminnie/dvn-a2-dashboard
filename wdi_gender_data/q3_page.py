from __future__ import annotations

import streamlit as st

from src import views
from src.load import get_obs, get_status

status = get_status()

with st.container(key="law_vs_reality"):
    views.render_law_vs_reality(status)

st.page_link("q4_page.py", label="Next question →")

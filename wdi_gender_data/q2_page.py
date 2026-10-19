from __future__ import annotations

import streamlit as st

from src import views
from src.load import get_obs, get_status

obs = get_obs()

with st.container(key="law_vs_outcomes"):
    views.render_law_vs_outcomes(obs)

st.page_link("q3_page.py", label="Next question →")

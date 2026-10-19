from __future__ import annotations

import streamlit as st

from src import views
from src.load import get_obs, get_status

obs = get_obs()
status = get_status()

with st.container(key="evidence_breaks"):
    views.render_evidence_breaks(obs, status)

st.page_link("about_page.py", label="About the data →")

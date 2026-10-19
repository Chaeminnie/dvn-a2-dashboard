from __future__ import annotations

import streamlit as st

from src import views
from src.load import get_obs, get_status

status = get_status()

with st.container(key="what_can_we_see"):
    views.render_what_can_we_see(status)

st.page_link("q2_page.py", label="Next question →")

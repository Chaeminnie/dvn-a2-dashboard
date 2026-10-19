from __future__ import annotations

import streamlit as st

from src import ui, views
from src.load import get

voters = get("voter_groups")

with st.container(key="who_divides_voters"):
    views.render_who_divides(voters)

st.page_link("q2_page.py", label="Next question →")

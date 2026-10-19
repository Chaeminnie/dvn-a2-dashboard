from __future__ import annotations

import streamlit as st

from src import ui, views
from src.load import get

monthly = get("search_monthly")
voters = get("voter_groups")

with st.container(key="phrase_and_gap"):
    views.render_phrase_and_gap(monthly, voters)

st.page_link("q4_page.py", label="Next question →")

from __future__ import annotations

import streamlit as st

from src import ui

st.set_page_config(page_title="Who divides American voters?", layout="wide")
ui.inject_css()

pages = [
    st.Page("intro_page.py", title="Start here", default=True),
    st.Page("q1_page.py", title="1 · What divides voters most?"),
    st.Page("q2_page.py", title="2 · How did states move?"),
    st.Page("q3_page.py", title="3 · Did the gap change after a phrase took off?"),
    st.Page("q4_page.py", title="4 · Did states that searched more move differently?"),
    st.Page("about_page.py", title="About the data"),
]
st.navigation(pages, position="sidebar").run()

from __future__ import annotations

import streamlit as st

from src import ui

st.set_page_config(page_title="Gender equality in the data", layout="wide")
ui.inject_css()

pages = [
    st.Page("intro_page.py", title="Start here", default=True),
    st.Page("q1_page.py", title="1 · What can we actually see?"),
    st.Page("q2_page.py", title="2 · Do laws change faster than outcomes?"),
    st.Page("q3_page.py", title="3 · Where do law and reality seem out of step?"),
    st.Page("q4_page.py", title="4 · Where does the evidence break off?"),
    st.Page("about_page.py", title="About the data"),
]
st.navigation(pages, position="sidebar").run()

from __future__ import annotations

import streamlit as st

from src import ui

st.set_page_config(page_title="Rules and Cases", layout="wide")
ui.inject_css()

pages = [
    st.Page("intro_page.py", title="Start here", default=True),
    st.Page("q1_page.py", title="1 · Who moved first?"),
    st.Page("q2_page.py", title="2 · How did governments’ response differ across variants?"),
    st.Page("q3_page.py", title="3 · Did people move before the rules?"),
    st.Page("q4_page.py", title="4 · How did outcomes differ by response timing?"),
    st.Page("about_page.py", title="About the data"),
]
st.navigation(pages, position="sidebar").run()

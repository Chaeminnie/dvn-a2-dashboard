"""Shared page furniture: styling, source attribution, downloads, filters."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.data import VARIANTS as _VARIANTS

DATE_LABEL = "Latest observation"
DOWNLOAD_LABEL = "Download filtered data"
EMPTY_MESSAGE = "No observations match the selected filters."
VARIANTS = list(_VARIANTS)

SOURCES = {
    "covariants_distribution": (
        "CoVariants: per-country variant distributions (perCountryData.json)",
        "CoVariants (Hodcroft Lab, University of Bern; Nextstrain and GISAID sequence data)"),
    "oxcgrt_national": (
        "Oxford COVID-19 Government Response Tracker: OxCGRT compact national dataset (v1)",
        "Blavatnik School of Government, University of Oxford"),
    "owid_covid_dataset": (
        "COVID-19 Dataset by Our World in Data (owid-covid-data.csv)",
        "Our World in Data"),
    "google_mobility_mirror": (
        "COVID-19 Mobility Data Aggregator: Google country reports (mobility_report_countries.csv)",
        "ActiveConclusion (GitHub mirror of Google COVID-19 Community Mobility Reports)"),
    "natural_earth_boundaries": (
        "world-atlas countries-110m (Natural Earth country boundaries, public domain)",
        "Natural Earth, packaged by Mike Bostock (world-atlas)"),
}
CORE = ["covariants_distribution", "oxcgrt_national", "owid_covid_dataset", "google_mobility_mirror"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
html, body, .stApp, .stApp :not([data-testid="stIconMaterial"]):not(svg):not(path) { font-family: 'Inter', 'Source Sans Pro', sans-serif; }
.block-container { max-width: 1240px; padding-top: 3.2rem; padding-bottom: 4rem; }
h1, h2, h3 { font-weight: 400 !important; letter-spacing: -0.025em; }
h1 { font-size: clamp(2rem, 4.4vw, 3.4rem) !important; line-height: 1.06 !important; }
h2 { font-size: clamp(1.6rem, 2.8vw, 2.3rem) !important; line-height: 1.12 !important; }
.eyebrow { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: #6c6c72; margin: 0 0 4px; }
.found { font-size: 21px; font-weight: 500; line-height: 1.35; letter-spacing: -0.01em; max-width: 46rem; border-left: 3px solid #6c6c72; padding-left: 14px; margin: 12px 0 22px; }
.how { font-size: 14px; line-height: 1.55; }
.how ul { padding-left: 18px; margin: 4px 0 0; }
.meta { font-size: 12px; color: #6c6c72; }
.big { font-size: clamp(4rem, 10vw, 9rem); font-weight: 300; letter-spacing: -.05em; line-height: .9; }
.dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:-1px; }
.legend { display:flex; flex-wrap:wrap; gap:4px 18px; font-size:12px; color:#6c6c72; margin: 4px 0 6px; }
[data-testid="stMetricValue"] { font-weight: 400; letter-spacing: -.02em; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 0; }
div[class*="st-key-who_moved_first"], div[class*="st-key-response_differs"],
div[class*="st-key-people_vs_rules"], div[class*="st-key-outcomes_by_timing"] {
  padding: 0.5rem 0 1.6rem; }
.stButton > button, .stDownloadButton > button { border-radius: 0; }
.frame { border-bottom: 1px solid #e4e4e7; padding: 3.5rem 0 2.5rem; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def dot(colour: str, text: str) -> str:
    return f'<span><span class="dot" style="background:{colour};border:1px solid #d5d5da"></span>{text}</span>'


def legend(*items: tuple[str, str]) -> None:
    st.markdown('<div class="legend">' + "".join(dot(c, t) for c, t in items) + "</div>", unsafe_allow_html=True)


def attribution(ids: list[str]) -> None:
    lines = "\n".join(f"- {SOURCES[i][0]}, {SOURCES[i][1]}" for i in ids)
    st.caption("Sources:\n" + lines)


def latest_caption(frame: pd.DataFrame, column: str) -> None:
    latest = frame[column].max() if len(frame) else "not available"
    st.caption(f"{DATE_LABEL}: {latest}")


def download(frame: pd.DataFrame, key: str, name: str) -> None:
    st.download_button(DOWNLOAD_LABEL, data=frame.to_csv(index=False).encode("utf-8"),
                       file_name=name, mime="text/csv", key=key)


def seed(key: str, value) -> None:
    """Give a widget its initial value through session state (no default argument)."""
    if key not in st.session_state:
        st.session_state[key] = value


def highlight_options(frame: pd.DataFrame) -> list[str]:
    return ["None"] + sorted(frame["country"].unique())

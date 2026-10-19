"""Shared page furniture: styling, source attribution, downloads, filters."""

from __future__ import annotations

import pandas as pd
import streamlit as st

DATE_LABEL = "Latest observation"
DOWNLOAD_LABEL = "Download filtered data"
EMPTY_MESSAGE = "No observations match the selected filters."

SOURCES = {
    "wbl_law_index": (
        "Women, Business and the Law Index Score (SG.LAW.INDX), WBL 1.0 series, WDI Database Archives",
        "World Bank (Women, Business and the Law)"),
    "ilo_labour_force": (
        "Labor force participation rate, female and male, modeled ILO estimate (SL.TLF.CACT.FE.ZS, SL.TLF.CACT.MA.ZS)",
        "International Labour Organization (ILOSTAT), published through World Bank WDI"),
    "unesco_enrolment": (
        "School enrollment, secondary, female (% gross) (SE.SEC.ENRR.FE)",
        "UNESCO Institute for Statistics, published through World Bank WDI"),
    "ipu_parliament": (
        "Proportion of seats held by women in national parliaments (SG.GEN.PARL.ZS)",
        "Inter-Parliamentary Union, published through World Bank WDI"),
    "global_findex": (
        "Account ownership at a financial institution or with a mobile-money-service provider, female (FX.OWN.TOTL.FE.ZS)",
        "Global Findex Database, World Bank"),
    "wdi_country_metadata": (
        "World Development Indicators country metadata: region and income group (Metadata_Country)",
        "World Bank"),
}
ALL_SOURCES = list(SOURCES)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
html, body, .stApp, .stApp :not([data-testid="stIconMaterial"]):not(svg):not(path) { font-family: 'Inter', 'Source Sans Pro', sans-serif; }
.block-container { max-width: 1240px; padding-top: 3.2rem; padding-bottom: 4rem; }
h1, h2, h3 { font-weight: 400 !important; letter-spacing: -0.02em; color: #1f3a5f; }
h1 { font-size: clamp(2rem, 4.2vw, 3.2rem) !important; line-height: 1.08 !important; }
h2 { font-size: clamp(1.5rem, 2.6vw, 2.1rem) !important; line-height: 1.14 !important; }
.eyebrow { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: #6b6a63; margin: 0 0 4px; }
.found { font-size: 21px; font-weight: 500; line-height: 1.35; letter-spacing: -0.01em; max-width: 46rem; border-left: 3px solid #6b6a63; padding-left: 14px; margin: 12px 0 22px; }
.meta { font-size: 12px; color: #6b6a63; }
.lede { font-size: 1.15rem; line-height: 1.5; max-width: 46rem; }
.legend { display:flex; flex-wrap:wrap; gap:4px 18px; font-size:12px; color:#6b6a63; margin: 4px 0 6px; }
.dot { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:6px; vertical-align:-1px; border:1px solid #d5d1c4; }
.card { background:#f1eee5; border-radius:6px; padding:12px 14px; font-size:14px; line-height:1.5; }
[data-testid="stMetricValue"] { font-weight: 400; letter-spacing: -.02em; }
div[class*="st-key-what_can_we_see"], div[class*="st-key-law_vs_outcomes"],
div[class*="st-key-law_vs_reality"], div[class*="st-key-evidence_breaks"] {
  padding: 0.5rem 0 1.6rem; }
.stButton > button, .stDownloadButton > button { border-radius: 6px; }
.frame { border-bottom: 1px solid #ddd8c9; padding: 2.6rem 0 2rem; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def swatch(colour: str, text: str) -> str:
    return f'<span><span class="dot" style="background:{colour}"></span>{text}</span>'


def legend(*items: tuple[str, str]) -> None:
    st.markdown('<div class="legend">' + "".join(swatch(c, t) for c, t in items) + "</div>", unsafe_allow_html=True)


def attribution(ids: list[str]) -> None:
    lines = "\n".join(f"- {SOURCES[i][0]}, {SOURCES[i][1]}" for i in ids)
    st.caption("Sources:\n" + lines)


def latest_caption(value) -> None:
    st.caption(f"{DATE_LABEL}: {value}")


def download(frame: pd.DataFrame, key: str, name: str) -> None:
    st.download_button(DOWNLOAD_LABEL, data=frame.drop(columns=["year"], errors="ignore").to_csv(index=False).encode("utf-8"),
                       file_name=name, mime="text/csv", key=key)


def seed(key: str, value) -> None:
    """Give a widget its initial value through session state (no default argument)."""
    if key not in st.session_state:
        st.session_state[key] = value

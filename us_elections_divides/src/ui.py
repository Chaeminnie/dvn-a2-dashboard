"""Shared page furniture: colours, styling, source attribution, downloads, small helpers."""

from __future__ import annotations

import pandas as pd
import streamlit as st

DATE_LABEL = "Latest observation"
DOWNLOAD_LABEL = "Download filtered data"
EMPTY_MESSAGE = "No observations match the selected filters."

# Colour roles: blue and red mean which way voters lean, amber means how big a divide is, teal means how much people searched.
BG, SURF, FG, MUT = "#0d0f13", "#161920", "#eceef2", "#98a0b0"
LINE, GRID = "#272b35", "#20242c"
DEM, REP, MID = "#5b8def", "#ef6a5b", "#2b2f3a"
AMBER, RAMP0, TEAL = "#f2c14e", "#1b1e27", "#38c1b3"
NODATA = "#3a3f4b"

SOURCES = {
    "ces": (
        "Cumulative CES Common Content (Cooperative Election Study), V12, doi:10.7910/DVN/II2DB6",
        "Shiro Kuriwaki, Harvard Dataverse"),
    "medsl_president": (
        "County Presidential Election Returns 2000-2024 (countypres_2000-2024), version 2026-02-25",
        "MIT Election Data and Science Lab"),
    "google_trends": (
        "Google Trends: interest over time and interest by region, United States, five search terms",
        "Google Trends (Google LLC)"),
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
html, body, .stApp, .stApp :not([data-testid="stIconMaterial"]):not(svg):not(path) {{ font-family: 'Inter', 'Source Sans Pro', sans-serif; }}
.block-container {{ max-width: 1240px; padding-top: 3.2rem; padding-bottom: 4rem; }}
h1, h2, h3 {{ font-weight: 500 !important; letter-spacing: -0.02em; color: {FG}; }}
h1 {{ font-size: clamp(2rem, 4.2vw, 3.1rem) !important; line-height: 1.08 !important; }}
h2 {{ font-size: clamp(1.45rem, 2.5vw, 2rem) !important; line-height: 1.15 !important; }}
.eyebrow {{ font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: {MUT}; margin: 0 0 4px; }}
.found {{ font-size: 21px; font-weight: 500; line-height: 1.35; letter-spacing: -0.01em; max-width: 46rem; border-left: 3px solid {MUT}; padding-left: 14px; margin: 12px 0 22px; }}
.lede {{ font-size: 1.15rem; line-height: 1.5; max-width: 44rem; color: {MUT}; }}
.legend {{ display:flex; flex-wrap:wrap; gap:4px 18px; font-size:12px; color:{MUT}; margin: 4px 0 6px; align-items:center; }}
.dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:-1px; }}
.ramp {{ display:inline-block; width:120px; height:8px; vertical-align:middle; margin:0 6px; }}
.turn {{ font-size: 12.5px; color: {MUT}; border-top: 1px solid {LINE}; padding-top: 8px; margin: 4px 0 10px; }}
.turn b {{ color: {FG}; font-weight: 500; }}
.card {{ background:{SURF}; border-radius:6px; padding:12px 14px; font-size:14px; line-height:1.5; }}
[data-testid="stMetricValue"] {{ font-weight: 400; letter-spacing: -.02em; }}
div[class*="st-key-who_divides_voters"], div[class*="st-key-state_shift"],
div[class*="st-key-phrase_and_gap"], div[class*="st-key-search_by_state"] {{
  border-bottom: 1px solid {LINE}; padding: 2.6rem 0 1.6rem; }}
div[class*="st-key-state_shift"] [data-testid="stVegaLiteChart"],
div[class*="st-key-search_by_state"] [data-testid="stVegaLiteChart"] {{ max-width: 900px; }}
.stButton > button, .stDownloadButton > button {{ border-radius: 6px; }}
.frame {{ border-bottom: 1px solid {LINE}; padding: 2.6rem 0 2rem; }}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------- colours ----
def _rgb(hex_: str) -> tuple[int, int, int]:
    h = hex_.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, float(t)))
    x, y = _rgb(a), _rgb(b)
    return "#%02x%02x%02x" % tuple(round(p + (q - p) * t) for p, q in zip(x, y))


def _ink(fill: str) -> str:
    r, g, b = _rgb(fill)
    return "#0d0f13" if (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.55 else "#ffffff"


def size_fill(t: float) -> tuple[str, str]:
    c = mix(RAMP0, AMBER, t)
    return c, _ink(c)


def lean_fill(v: float, limit: float) -> tuple[str, str]:
    """Blue for positive (Democratic), red for negative (Republican), grey in the middle."""
    t = max(-1.0, min(1.0, v / limit))
    c = mix(MID, DEM, t) if t >= 0 else mix(MID, REP, -t)
    return c, _ink(c)


def interest_fill(v: float) -> tuple[str, str]:
    c = mix(RAMP0, TEAL, v / 100)
    return c, _ink(c)


# -------------------------------------------------------------- widgets ----
def swatch(colour: str, text: str) -> str:
    return f'<span><span class="dot" style="background:{colour}"></span>{text}</span>'


def legend(*items: tuple[str, str]) -> None:
    st.markdown('<div class="legend">' + "".join(swatch(c, t) for c, t in items) + "</div>", unsafe_allow_html=True)


def ramp_legend(stops: list[str], left_label: str, right_label: str) -> None:
    """A colour ramp between two labels. `stops` are the gradient colours from left to right."""
    st.markdown(
        f'<div class="legend"><span>{left_label}</span><span class="ramp" style="background:linear-gradient(90deg,{",".join(stops)})"></span>'
        f'<span>{right_label}</span></div>', unsafe_allow_html=True)


def attribution(ids: list[str]) -> None:
    lines = "\n".join(f"- {SOURCES[i][0]}, {SOURCES[i][1]}" for i in ids)
    st.caption("Sources:\n" + lines)


def latest_caption(value) -> None:
    st.caption(f"{DATE_LABEL}: {value}")


def download(frame: pd.DataFrame, key: str, name: str) -> None:
    st.download_button(DOWNLOAD_LABEL, data=frame.to_csv(index=False).encode("utf-8"),
                       file_name=name, mime="text/csv", key=key)


def seed(key: str, value) -> None:
    """Give a widget its initial value through session state (no default argument)."""
    if key not in st.session_state:
        st.session_state[key] = value


def found(text: str) -> None:
    st.markdown(f'<div class="found">{text}</div>', unsafe_allow_html=True)


def sgn(v: float, digits: int = 1) -> str:
    r = round(float(v), digits)
    return ("+" if r > 0 else "−" if r < 0 else "") + f"{abs(r):.{digits}f}"

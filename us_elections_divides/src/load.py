"""Cached data loading for the Streamlit pages."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"


def use_sample() -> bool:
    return os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1"


def pick(name: str) -> Path:
    path = DATA / f"processed_{name}.csv"
    return DATA / f"sample_{name}.csv" if use_sample() or not path.exists() else path


@st.cache_data
def _load(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"date": str, "state_code": str}, keep_default_na=False, na_values=[""])
    if "interest" in frame:
        frame["interest"] = frame["interest"].astype("Int64")
    if "previous_election_year" in frame:
        frame["previous_election_year"] = frame["previous_election_year"].astype("Int64")
    return frame


def get(name: str) -> pd.DataFrame:
    return _load(str(pick(name)))


def records(frame: pd.DataFrame) -> list[dict]:
    """Plain Python records with missing values as None (JSON safe)."""
    out = []
    for row in frame.to_dict("records"):
        out.append({k: (None if pd.isna(v) else (v.item() if hasattr(v, "item") else v)) for k, v in row.items()})
    return out

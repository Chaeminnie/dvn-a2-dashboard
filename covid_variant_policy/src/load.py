"""Cached data loading for the Streamlit pages."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"


def use_sample() -> bool:
    return os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1"


def pick(sample: str, processed: str) -> Path:
    path = DATA / processed
    return DATA / sample if use_sample() or not path.exists() else path


@st.cache_data
def load_panel(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"country_code": str, "date": str, "event_week": str, "sequences": "Int64"},
                        keep_default_na=False, na_values=[""])
    return frame.sort_values(["variant", "country", "rel_week"]).reset_index(drop=True)


@st.cache_data
def load_summary(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"country_code": str, "event_week": str, "policy_week": "Int64",
                                     "cases_week": "Int64", "policy_minus_cases": "Int64",
                                     "peak_cases_week": "Int64"},
                        keep_default_na=False, na_values=[""])
    return frame.sort_values(["variant", "country"]).reset_index(drop=True)


def get_panel() -> pd.DataFrame:
    return load_panel(str(pick("sample.csv", "processed.csv")))


def get_summary() -> pd.DataFrame:
    return load_summary(str(pick("sample_summary.csv", "processed_summary.csv")))


def records(frame: pd.DataFrame) -> list[dict]:
    """Plain Python records with missing values as None (JSON safe)."""
    out = []
    for row in frame.to_dict("records"):
        out.append({k: (None if pd.isna(v) else (v.item() if hasattr(v, "item") else v)) for k, v in row.items()})
    return out


def jitter(n: int) -> np.ndarray:
    return np.sin(np.arange(n) * 12.9898) * 0.28

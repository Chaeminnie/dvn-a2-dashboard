"""Cached data loading for the Streamlit pages."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"


def use_sample() -> bool:
    return os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1"


def pick(sample: str, processed: str) -> Path:
    path = DATA / processed
    return DATA / sample if use_sample() or not path.exists() else path


@st.cache_data
def load_obs(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"country_code": str, "date": str}, keep_default_na=False, na_values=[""])
    frame["year"] = frame["date"].str[:4].astype(int)
    return frame


@st.cache_data
def load_status(path: str) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"country_code": str, "latest_date": str, "latest_year": "Int64",
                                    "first_year": "Int64", "years_with_value": "Int64", "years_behind": "Int64"},
                       keep_default_na=False, na_values=[""])


def get_obs() -> pd.DataFrame:
    return load_obs(str(pick("sample.csv", "processed.csv")))


def get_status() -> pd.DataFrame:
    return load_status(str(pick("sample_status.csv", "processed_status.csv")))


def records(frame: pd.DataFrame) -> list[dict]:
    """Plain Python records with missing values as None (JSON safe)."""
    out = []
    for row in frame.to_dict("records"):
        out.append({k: (None if pd.isna(v) else (v.item() if hasattr(v, "item") else v)) for k, v in row.items()})
    return out

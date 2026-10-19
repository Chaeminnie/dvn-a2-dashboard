"""Acquire, transform and validate the dashboard's two datasets.

observations   one row per country, indicator and year (2000 onward): the values that exist.
country_status one row per country and indicator (every combination, including those with no
               value ever recorded): the latest year, how far behind it is, and a status label.

Modes
  python -m src.data               build from the World Bank bulk CSV files in data/raw/
  DASHBOARD_SAMPLE_MODE=1 python -m src.data
                                   regenerate the processed files from the bundled samples (offline)
  python -m src.data --acquire     download fresh bulk files into data/raw/ (needs a network)
  python -m src.data --validate    check the processed files and stop
  python -m src.data --make-sample cut data/sample*.csv from the processed files
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import zipfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
SAMPLE_OBS, SAMPLE_STATUS = DATA / "sample.csv", DATA / "sample_status.csv"
PROCESSED_OBS, PROCESSED_STATUS = DATA / "processed.csv", DATA / "processed_status.csv"

FIRST_YEAR = 2000          # observations table starts here; country_status uses the whole history
# code, short name, kind, unit, years behind the newest year before a value counts as "Behind"
INDICATORS = [
    ("SG.LAW.INDX", "Law score (WBL 1.0)", "law", "score, 0 to 100", 4),
    ("SL.TLF.CACT.FE.ZS", "Women in the labour force", "outcome", "% of women aged 15+", 4),
    ("SL.TLF.CACT.MA.ZS", "Men in the labour force", "outcome", "% of men aged 15+", 4),
    ("SE.SEC.ENRR.FE", "Girls in secondary school", "outcome", "% gross enrolment ratio", 4),
    ("SG.GEN.PARL.ZS", "Women in parliament", "outcome", "% of seats", 4),
    ("FX.OWN.TOTL.FE.ZS", "Women with an account", "outcome", "% of women aged 15+", 6),
]
NAME = {c: n for c, n, *_ in INDICATORS}
KIND = {c: k for c, _, k, *_ in INDICATORS}
UNIT = {c: u for c, _, _, u, _ in INDICATORS}
STALE = {c: s for c, *_, s in INDICATORS}
# The WDI archive file for SG.LAW.INDX holds weighted points, not the 0-100 score its description states.
# The most points a country can score is 4,100 up to 2019 and 3,400 / 2,600 / 2,100 / 1,600 in 2020-2023
# (10 to 14 countries tie at exactly that maximum in each of those years). Points are divided by that
# maximum and multiplied by 100. The questions behind the score changed in 2020 and again in 2022, so the
# scale breaks there; see the README.
LAW_MAX_POINTS = {2020: 3400, 2021: 2600, 2022: 2100, 2023: 1600}
LAW_MAX_DEFAULT = 4100
BULK_URL = "https://api.worldbank.org/v2/en/indicator/{code}?downloadformat=csv"

REGIONS = ["East Asia & Pacific", "Europe & Central Asia", "Latin America & Caribbean",
           "Middle East & North Africa", "North America", "South Asia", "Sub-Saharan Africa"]
INCOMES = ["Low income", "Lower middle income", "Upper middle income", "High income"]
STATUSES = ["Current", "Behind", "No value in WDI"]

OBS_COLUMNS = ["date", "country_code", "country", "region", "income_group", "indicator_code",
               "indicator", "value", "unit"]
STATUS_COLUMNS = ["country_code", "country", "region", "income_group", "indicator_code", "indicator",
                  "kind", "latest_date", "latest_year", "latest_value", "first_year", "years_with_value",
                  "newest_year_in_wdi", "years_behind", "status"]


def acquire() -> None:
    """Download each indicator's bulk CSV zip from the World Bank into data/raw/."""
    RAW.mkdir(parents=True, exist_ok=True)
    for code, *_ in INDICATORS:
        url = BULK_URL.format(code=code)
        try:
            with urlopen(url, timeout=60) as response:
                payload = response.read()
        except (URLError, TimeoutError) as error:
            sys.exit(f"Could not fetch {url}: {error}. Use DASHBOARD_SAMPLE_MODE=1 for the bundled sample.")
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for member in archive.namelist():
                base = Path(member).name
                if base.startswith("API_"):
                    (RAW / f"API_{code}.csv").write_bytes(archive.read(member))
                elif base.startswith("Metadata_Country") and not (RAW / "Metadata_Country.csv").exists():
                    (RAW / "Metadata_Country.csv").write_bytes(archive.read(member))
        print(f"Fetched {code}")


def read_countries() -> pd.DataFrame:
    """Countries only (aggregates have no region), with the World Bank region and income group."""
    meta = pd.read_csv(RAW / "Metadata_Country.csv", encoding="utf-8-sig", keep_default_na=False, na_values=[""])
    meta = meta.loc[:, ~meta.columns.str.startswith("Unnamed")]
    meta = meta[meta["Region"].notna() & meta["IncomeGroup"].notna()]
    return meta.rename(columns={"Country Code": "country_code", "TableName": "country", "Region": "region",
                                "IncomeGroup": "income_group"})[["country_code", "country", "region", "income_group"]]


def read_indicator(code: str) -> pd.DataFrame:
    path = RAW / f"API_{code}.csv"
    frame = pd.read_csv(path, skiprows=4, encoding="utf-8-sig", keep_default_na=False, na_values=[""])
    frame = frame.loc[:, ~frame.columns.str.startswith("Unnamed")]
    years = [c for c in frame.columns if c.isdigit()]
    long = frame.melt(id_vars=["Country Code"], value_vars=years, var_name="year", value_name="value")
    long = long.dropna(subset=["value"]).rename(columns={"Country Code": "country_code"})
    long["year"] = long["year"].astype(int)
    long["indicator_code"] = code
    if code == "SG.LAW.INDX":
        top = long["year"].map(lambda y: LAW_MAX_POINTS.get(y, LAW_MAX_DEFAULT))
        long["value"] = long["value"] / top * 100
    return long


def build(countries: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    pieces = [read_indicator(code) for code, *_ in INDICATORS]
    long = pd.concat(pieces, ignore_index=True)
    long = long[long["country_code"].isin(countries["country_code"])]
    long = long.merge(countries, on="country_code", how="left")

    obs = long[long["year"] >= FIRST_YEAR].copy()
    obs["date"] = obs["year"].astype(str) + "-12-31"
    obs["indicator"] = obs["indicator_code"].map(NAME)
    obs["unit"] = obs["indicator_code"].map(UNIT)
    obs["value"] = obs["value"].round(4)
    obs = obs[OBS_COLUMNS].sort_values(["indicator_code", "country", "date"]).reset_index(drop=True)

    grid = pd.MultiIndex.from_product([countries["country_code"], [c for c, *_ in INDICATORS]],
                                      names=["country_code", "indicator_code"]).to_frame(index=False)
    stats = long.sort_values("year").groupby(["country_code", "indicator_code"]).agg(
        latest_year=("year", "max"), first_year=("year", "min"), years_with_value=("year", "size"),
        latest_value=("value", "last")).reset_index()
    status = grid.merge(stats, on=["country_code", "indicator_code"], how="left").merge(countries, on="country_code")
    newest = status.groupby("indicator_code")["latest_year"].max()
    status["newest_year_in_wdi"] = status["indicator_code"].map(newest).astype(int)
    status["years_behind"] = status["newest_year_in_wdi"] - status["latest_year"]
    limit = status["indicator_code"].map(STALE)
    status["status"] = "No value in WDI"
    has = status["latest_year"].notna()
    status.loc[has & (status["years_behind"] <= limit), "status"] = "Current"
    status.loc[has & (status["years_behind"] > limit), "status"] = "Behind"
    status["indicator"] = status["indicator_code"].map(NAME)
    status["kind"] = status["indicator_code"].map(KIND)
    status["latest_date"] = status["latest_year"].map(lambda y: None if pd.isna(y) else f"{int(y)}-12-31")
    status["latest_value"] = status["latest_value"].round(4)
    for col in ["latest_year", "first_year", "years_with_value", "years_behind"]:
        status[col] = status[col].astype("Int64")
    status = status[STATUS_COLUMNS].sort_values(["indicator_code", "country"]).reset_index(drop=True)
    return obs, status


def read_obs(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"country_code": str, "date": str}, keep_default_na=False, na_values=[""])


def read_status(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"country_code": str, "latest_date": str, "latest_year": "Int64",
                                    "first_year": "Int64", "years_with_value": "Int64", "years_behind": "Int64"},
                       keep_default_na=False, na_values=[""])


def validate(obs: pd.DataFrame, status: pd.DataFrame) -> None:
    if list(obs.columns) != OBS_COLUMNS:
        raise ValueError(f"observations columns differ: {list(obs.columns)}")
    if list(status.columns) != STATUS_COLUMNS:
        raise ValueError(f"country_status columns differ: {list(status.columns)}")
    if obs.duplicated(["date", "country_code", "indicator_code"]).any():
        raise ValueError("Duplicate observation keys")
    if status.duplicated(["country_code", "indicator_code"]).any():
        raise ValueError("Duplicate status keys")
    if obs["value"].isna().any() or not obs["value"].between(0, 200).all():
        raise ValueError("Observation values must exist and lie between 0 and 200")
    if not set(obs["indicator_code"]) <= set(NAME):
        raise ValueError("Unexpected indicator code")
    if not set(status["status"]) <= set(STATUSES):
        raise ValueError("Unexpected status label")
    if len(status) != status["country_code"].nunique() * len(INDICATORS):
        raise ValueError("country_status must hold every country and indicator")
    # the two tables must agree wherever the latest year is inside the observation window
    latest = obs.assign(year=obs["date"].str[:4].astype(int)).groupby(["country_code", "indicator_code"])["year"].max()
    check = status.dropna(subset=["latest_year"]).set_index(["country_code", "indicator_code"])["latest_year"]
    inside = check[check >= FIRST_YEAR].astype(int)
    if not inside.equals(latest.reindex(inside.index)) or len(latest) != len(inside):
        raise ValueError("Latest years in country_status disagree with observations")


# The offline sample keeps every fifth country (by code) plus the countries the introduction and the manifest name,
# with all of their indicators and years, so every view still has something to draw.
SAMPLE_STEP = 5
SAMPLE_KEEP = ["Afghanistan", "Australia", "Brazil", "India", "Japan", "Kenya", "Nigeria", "Pakistan",
               "Somalia, Fed. Rep.", "Sweden", "Yemen, Rep.", "Zimbabwe"]


def make_sample() -> None:
    obs, status = read_obs(PROCESSED_OBS), read_status(PROCESSED_STATUS)
    countries = status[["country_code", "country"]].drop_duplicates().sort_values("country_code")
    keep = set(countries["country_code"].iloc[::SAMPLE_STEP]) | set(countries.loc[countries["country"].isin(SAMPLE_KEEP), "country_code"])
    obs[obs["country_code"].isin(keep)].to_csv(SAMPLE_OBS, index=False)
    status[status["country_code"].isin(keep)].to_csv(SAMPLE_STATUS, index=False)
    print(f"Cut {SAMPLE_OBS.name} and {SAMPLE_STATUS.name}: {len(keep)} of {len(countries)} countries")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--make-sample", action="store_true")
    args = parser.parse_args()
    sample_mode = os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1"
    if args.acquire:
        if sample_mode:
            parser.error("Unset DASHBOARD_SAMPLE_MODE before acquiring live data")
        acquire()
        return
    if args.validate:
        validate(read_obs(PROCESSED_OBS), read_status(PROCESSED_STATUS))
        print("Processed data valid")
        return
    if args.make_sample:
        make_sample()
        return
    if sample_mode:
        obs, status = read_obs(SAMPLE_OBS), read_status(SAMPLE_STATUS)
    else:
        obs, status = build(read_countries())
    validate(obs, status)
    PROCESSED_OBS.parent.mkdir(parents=True, exist_ok=True)
    obs.to_csv(PROCESSED_OBS, index=False)
    status.to_csv(PROCESSED_STATUS, index=False)
    print(f"Validated and wrote {len(obs)} observations and {len(status)} status rows")


if __name__ == "__main__":
    main()

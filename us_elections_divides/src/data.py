"""Build the four datasets behind the dashboard.

voter_groups       survey vote choice by gender, income and region, each within age bands, per election
state_results      official presidential results per state (two-party shares and margin), 2016 2020 2024
search_monthly     Google Trends monthly interest in five political phrases, 2015-01 to 2026-09
state_search_shift Google Trends interest per state (2020-11-04 to 2024-11-04) next to the state's margin shift

Modes
  python -m src.data               build from the raw files in data/raw/
  DASHBOARD_SAMPLE_MODE=1 python -m src.data
                                   regenerate the processed files from the bundled samples (offline)
  python -m src.data --validate    check the processed files and stop
  python -m src.data --make-sample cut data/sample*.csv from the processed files

The raw files are manual downloads (see README.md, "Data and pipeline"); nothing is fetched by this module.
The voter_groups table is the output of src/ces_aggregate.py run on the Cumulative CES Common Content.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"

NAMES = ["voter_groups", "state_results", "search_monthly", "state_search_shift"]
SAMPLE = {n: DATA / f"sample_{n}.csv" for n in NAMES}
PROCESSED = {n: DATA / f"processed_{n}.csv" for n in NAMES}

ELECTION_DAY = {2016: "2016-11-08", 2018: "2018-11-06", 2020: "2020-11-03", 2022: "2022-11-08", 2024: "2024-11-05"}
ELECTION_TYPE = {2016: "Presidential", 2018: "Midterm", 2020: "Presidential", 2022: "Midterm", 2024: "Presidential"}
VOTE_FOR = {"Presidential": "President", "Midterm": "U.S. House"}
PRESIDENTIAL_YEARS = [2016, 2020, 2024]

KEYWORDS = ["tradwife", "manosphere", "MAGA", "inflation", "border crisis"]
KW_FILE = {"tradwife": "tradwife", "manosphere": "manosphere", "MAGA": "maga", "inflation": "inflation",
           "border crisis": "border_crisis"}
TREND_FIRST, TREND_LAST = "2015-01-01", "2026-09-01"     # October 2026 was still running when exported
STATE_WINDOW_END = "2024-11-04"                           # by-state export covers 2020-11-04 to 2024-11-04
SMALL_STATE_VOTES = 600_000                               # fewer than this many two-party votes in 2024

REGION = {}
for _region, _states in {"Northeast": "CT ME MA NH RI VT NJ NY PA", "Midwest": "IL IN MI OH WI IA KS MN MO NE ND SD",
                         "South": "DE DC FL GA MD NC SC VA WV AL KY MS TN AR LA OK TX",
                         "West": "AZ CO ID MT NV NM UT WY AK CA HI OR WA"}.items():
    for _s in _states.split():
        REGION[_s] = _region

VOTER_COLUMNS = ["date", "election_year", "election_type", "vote_for", "factor", "group", "age_band", "n_two_party",
                 "dem_share_pct", "n_validated", "validated_turnout_pct", "low_n"]
STATE_COLUMNS = ["date", "election_year", "state_code", "state", "region", "dem_votes", "rep_votes",
                 "dem_two_party_pct", "margin_pp", "previous_election_year", "previous_margin_pp", "shift_pp"]
MONTH_COLUMNS = ["date", "keyword", "interest"]
SHIFT_COLUMNS = ["date", "keyword", "state_code", "state", "region", "interest", "small_state", "margin_2020",
                 "margin_2024", "shift_2020_2024"]


# ------------------------------------------------------------------ build ----
def build_voter_groups() -> pd.DataFrame:
    raw = pd.read_csv(RAW / "ces_aggregates.csv")
    raw["election_year"] = raw["year"].astype(int)
    raw["date"] = raw["election_year"].map(ELECTION_DAY)
    raw["election_type"] = raw["election_year"].map(ELECTION_TYPE)
    raw["vote_for"] = raw["election_type"].map(VOTE_FOR)
    return raw[VOTER_COLUMNS].sort_values(["election_year", "factor", "group", "age_band"]).reset_index(drop=True)


def build_state_results() -> pd.DataFrame:
    county = pd.read_csv(RAW / "countypres_2000-2024.csv", dtype={"county_fips": str})
    two = county[county["year"].isin(PRESIDENTIAL_YEARS) & county["party"].isin(["DEMOCRAT", "REPUBLICAN"])].copy()
    two["mode"] = two["mode"].fillna("NA")
    # Some counties carry a TOTAL row and also one row per voting mode; adding both would count votes twice.
    key = [two["year"], two["state_po"], two["county_fips"], two["party"]]
    has_total = (two["mode"] == "TOTAL").groupby(key).transform("any").astype(bool)
    two = two[~has_total | (two["mode"] == "TOTAL")]
    votes = two.groupby(["year", "state_po", "state", "party"])["candidatevotes"].sum().unstack("party").reset_index()
    out = pd.DataFrame({
        "election_year": votes["year"].astype(int),
        "state_code": votes["state_po"],
        "state": votes["state"].str.title().str.replace("Of", "of"),
        "dem_votes": votes["DEMOCRAT"].round().astype(int),
        "rep_votes": votes["REPUBLICAN"].round().astype(int),
    })
    out["date"] = out["election_year"].astype(str).map(lambda y: ELECTION_DAY[int(y)])
    out["region"] = out["state_code"].map(REGION)
    total = out["dem_votes"] + out["rep_votes"]
    out["dem_two_party_pct"] = (100 * out["dem_votes"] / total).round(2)
    out["margin_pp"] = (200 * out["dem_votes"] / total - 100).round(2)      # Democratic minus Republican share
    # Shift = margin minus the margin at the previous presidential election (four years earlier). 2016 has none.
    out["previous_election_year"] = (out["election_year"] - 4).where(out["election_year"] > 2016).astype("Int64")
    earlier = out.set_index(["election_year", "state_code"])["margin_pp"]
    keys = list(zip(out["previous_election_year"].astype("object"), out["state_code"]))
    out["previous_margin_pp"] = [earlier.get((int(y), c)) if pd.notna(y) else np.nan for y, c in keys]
    out["shift_pp"] = (out["margin_pp"] - out["previous_margin_pp"]).round(2)
    return out[STATE_COLUMNS].sort_values(["election_year", "state_code"]).reset_index(drop=True)


def build_search_monthly() -> pd.DataFrame:
    frames = []
    for kw in KEYWORDS:
        f = pd.read_csv(RAW / "trends" / f"time_{KW_FILE[kw]}.csv")
        f.columns = ["date", "interest"]
        f["keyword"] = kw
        frames.append(f)
    out = pd.concat(frames, ignore_index=True)
    out = out[(out["date"] >= TREND_FIRST) & (out["date"] <= TREND_LAST)]
    return out[MONTH_COLUMNS].sort_values(["keyword", "date"]).reset_index(drop=True)


def build_state_search_shift(states: pd.DataFrame) -> pd.DataFrame:
    wide = states.pivot(index="state_code", columns="election_year", values="margin_pp")
    wide.columns = [f"margin_{c}" for c in wide.columns]
    wide["shift_2020_2024"] = (wide["margin_2024"] - wide["margin_2020"]).round(2)
    info = states[states["election_year"] == 2024].set_index("state_code")
    wide["state"], wide["region"] = info["state"], info["region"]
    wide["small_state"] = np.where((info["dem_votes"] + info["rep_votes"]) < SMALL_STATE_VOTES, "Yes", "No")
    name_to_code = {n: c for c, n in info["state"].items()}
    name_to_code["District of Columbia"] = "DC"
    rows = []
    for kw in KEYWORDS:
        f = pd.read_csv(RAW / "trends" / f"state_{KW_FILE[kw]}.csv")
        f.columns = ["name", "interest"]
        f["state_code"] = f["name"].map(name_to_code)
        if f["state_code"].isna().any():
            raise ValueError(f"Unmatched state names in the {kw} file: {f.loc[f['state_code'].isna(), 'name'].tolist()}")
        f = wide.reset_index().merge(f[["state_code", "interest"]], on="state_code", how="left")   # missing stays missing
        f["keyword"] = kw
        rows.append(f)
    out = pd.concat(rows, ignore_index=True)
    out["date"] = STATE_WINDOW_END
    out["interest"] = out["interest"].astype("Int64")
    return out[SHIFT_COLUMNS].sort_values(["keyword", "state_code"]).reset_index(drop=True)


def build() -> dict[str, pd.DataFrame]:
    states = build_state_results()
    return {"voter_groups": build_voter_groups(), "state_results": states,
            "search_monthly": build_search_monthly(), "state_search_shift": build_state_search_shift(states)}


# ---------------------------------------------------------------- validate ----
def read(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, keep_default_na=False, na_values=[""], dtype={"date": str, "state_code": str})
    if "interest" in frame:
        frame["interest"] = frame["interest"].astype("Int64")
    if "previous_election_year" in frame:
        frame["previous_election_year"] = frame["previous_election_year"].astype("Int64")
    return frame


def validate(t: dict[str, pd.DataFrame]) -> None:
    v, s, m, x = t["voter_groups"], t["state_results"], t["search_monthly"], t["state_search_shift"]
    for name, frame, key in [("voter_groups", v, ["election_year", "factor", "group", "age_band"]),
                             ("state_results", s, ["election_year", "state_code"]),
                             ("search_monthly", m, ["keyword", "date"]),
                             ("state_search_shift", x, ["keyword", "state_code"])]:
        if frame.empty:
            raise ValueError(f"{name} is empty")
        if frame.duplicated(key).any():
            raise ValueError(f"{name} has duplicate keys {key}")
    if not v["dem_share_pct"].between(0, 100).all() or not v["validated_turnout_pct"].dropna().between(0, 100).all():
        raise ValueError("voter_groups shares must lie between 0 and 100")
    if set(v["election_year"]) != set(ELECTION_DAY):
        raise ValueError("voter_groups must cover 2016, 2018, 2020, 2022 and 2024")
    if (v["n_two_party"] < 1).any():
        raise ValueError("voter_groups has an empty cell")
    n_states = 51   # 50 states plus DC
    if s["shift_pp"].notna().sum() != 2 * n_states or s.loc[s["election_year"] == 2016, "shift_pp"].notna().any():
        raise ValueError("shift_pp must exist for 2020 and 2024 (51 states each) and be empty for 2016")
    if not s["margin_pp"].between(-100, 100).all() or (s.groupby("election_year")["state_code"].nunique() != n_states).any():
        raise ValueError("state_results must have 50 states plus DC in each election, with margins in -100..100")
    nat = s.groupby("election_year")[["dem_votes", "rep_votes"]].sum()
    # About 125 to 160 million votes are cast in a U.S. election, so a party total outside 60 to 100 million means double counting or missing rows.
    if not (60e6 < nat.to_numpy()).all() or not (nat.to_numpy() < 100e6).all():
        raise ValueError("State totals look wrong (votes counted twice or missing)")
    if not m["interest"].between(0, 100).all() or set(m["keyword"]) != set(KEYWORDS):
        raise ValueError("search_monthly values must be 0 to 100 for all five phrases")
    if not x["interest"].dropna().between(0, 100).all() or set(x["keyword"]) != set(KEYWORDS):
        raise ValueError("state_search_shift interest must be 0 to 100 for all five phrases")


# -------------------------------------------------------------------- main ----
def make_sample() -> None:
    for n in NAMES:
        read(PROCESSED[n]).to_csv(SAMPLE[n], index=False)
    print("Cut " + ", ".join(SAMPLE[n].name for n in NAMES))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--make-sample", action="store_true")
    args = parser.parse_args()
    if args.validate:
        validate({n: read(PROCESSED[n]) for n in NAMES})
        print("Processed data valid")
        return
    if args.make_sample:
        make_sample()
        return
    if os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1":
        tables = {n: read(SAMPLE[n]) for n in NAMES}
    else:
        tables = build()
    validate(tables)
    DATA.mkdir(parents=True, exist_ok=True)
    for n in NAMES:
        tables[n].to_csv(PROCESSED[n], index=False)
    print("Validated and wrote " + ", ".join(f"{len(tables[n])} {n} rows" for n in NAMES))


if __name__ == "__main__":
    main()

"""Acquire, transform and validate the variant-takeover event datasets.

Pipeline (one module so the lineage is inspectable):

    acquire()        download four public files into data/raw/ (live mode only)
    build_panel()    align them on "weeks around the week a variant family first
                     became the majority of sequenced samples" (one row per
                     country x variant x relative week)
    summarise()      derive one row per country x variant event: when did
                     containment tightening and the rise in cases start,
                     relative to the takeover week?
    validate_*()     stop the pipeline on any broken expectation
    main()           offline mode (DASHBOARD_SAMPLE_MODE=1) rebuilds both
                     processed files from the bundled sample; live mode runs
                     acquire -> build -> validate.

Presentation lives in views.py and app.py.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"

SAMPLE_PANEL = DATA / "sample.csv"
PROCESSED_PANEL = DATA / "processed.csv"
SAMPLE_SUMMARY = DATA / "sample_summary.csv"
PROCESSED_SUMMARY = DATA / "processed_summary.csv"

SOURCES = {
    "covariants.json": (
        "https://raw.githubusercontent.com/hodcroftlab/covariants/master/"
        "web/public/data/perCountryData.json"
    ),
    "oxcgrt.csv": (
        "https://raw.githubusercontent.com/OxCGRT/covid-policy-dataset/main/"
        "data/OxCGRT_compact_national_v1.csv"
    ),
    "owid_covid.csv": (
        "https://raw.githubusercontent.com/owid/covid-19-data/master/"
        "public/data/owid-covid-data.csv"
    ),
    "mobility.csv": (
        "https://raw.githubusercontent.com/ActiveConclusion/COVID19_mobility/"
        "master/google_reports/mobility_report_countries.csv"
    ),
}

# ---- analysis parameters (documented in README.md and the dashboard) -------
WINDOW = 8  # weeks before and after the takeover week
MIN_SEQUENCES = 30  # a week with fewer sequenced samples gives no variant share
MAJORITY = 0.5
BASELINE_WEEKS = (-8, -5)  # inclusive relative weeks used as the baseline
STRINGENCY_RISE = 5.0  # index points above baseline = "containment tightened"
CASE_RISE_RATIO = 1.5  # cases >= 1.5 x baseline = "cases rising"
CASE_RISE_FLOOR = 1.0  # ... and at least 1 case per million per day
# Only the first takeover of each family is used, within these event windows,
# so that "Omicron" means the BA.1/BA.2 displacement of Delta.
EVENT_WINDOWS = {
    "Alpha": ("2020-12-01", "2021-06-30"),
    "Delta": ("2021-03-01", "2021-12-31"),
    "Omicron": ("2021-11-01", "2022-04-30"),
}
VARIANTS = tuple(EVENT_WINDOWS)

# CoVariants / Google mobility country names -> OWID location names
NAME_FIXES = {
    "USA": "United States",
    "Czech Republic": "Czechia",
    "Democratic Republic of the Congo": "Democratic Republic of Congo",
    "Cabo Verde": "Cape Verde",
    "Myanmar (Burma)": "Myanmar",
    "Côte d'Ivoire": "Cote d'Ivoire",
    "The Bahamas": "Bahamas",
    "Timor-Leste": "East Timor",
}

PANEL_COLUMNS = [
    "date", "country_code", "country", "continent", "median_age", "variant",
    "event_week", "rel_week", "variant_share", "sequences", "stringency_index", "cases_per_million",
    "deaths_per_million", "workplace_mobility",
]
SUMMARY_COLUMNS = [
    "country_code", "country", "continent", "median_age", "variant", "event_week",
    "baseline_stringency", "baseline_cases_per_million", "policy_week", "cases_week",
    "policy_minus_cases", "sequence", "peak_cases_week", "peak_growth",
]
SEQUENCE_LABELS = (
    "Containment tightened first",
    "Cases rose first",
    "Same week",
    "Containment tightened, cases did not rise",
    "Cases rose, containment did not tighten",
    "Neither moved",
)


# =============================== acquisition ================================
def acquire() -> None:
    """Download the four raw files to data/raw/."""
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        try:
            with urlopen(url, timeout=120) as response:
                payload = response.read()
        except (URLError, TimeoutError) as error:
            sys.exit(
                f"Could not fetch {url}: {error}. Check your connection, or rerun "
                "with DASHBOARD_SAMPLE_MODE=1 to rebuild from the bundled sample."
            )
        (RAW / name).write_bytes(payload)
        print(f"Wrote {RAW / name} ({len(payload):,} bytes)")


# ================================ transform =================================
def _variant_shares(path: Path) -> pd.DataFrame:
    """Weekly share of each variant family among sequenced samples."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for region in payload["regions"]:
        for entry in region["distributions"]:
            for week in entry["distribution"]:
                counts = week["cluster_counts"]
                total = week["total_sequences"]
                for family in VARIANTS:
                    count = sum(v for k, v in counts.items() if f"({family}" in k or f" {family}" in k)
                    rows.append((entry["country"], week["week"], family, count, total))
    frame = pd.DataFrame(rows, columns=["covariants_name", "week", "variant", "count", "sequences"])
    frame["week"] = pd.to_datetime(frame["week"])
    # a country can appear in more than one regional block: keep the largest sample
    frame = (frame.sort_values("sequences", ascending=False)
             .drop_duplicates(["covariants_name", "week", "variant"]))
    frame = frame[frame["sequences"] >= MIN_SEQUENCES].copy()
    frame["variant_share"] = 100 * frame["count"] / frame["sequences"]
    return frame.drop(columns="count")


def _find_events(shares: pd.DataFrame) -> pd.DataFrame:
    """First sustained majority week of each family in each country.

    A takeover is the first week a family reaches >=50% of sequences, where
    the next two sequenced weeks average >=50% (not a one-week blip) and the
    family was below 50% at least eight weeks earlier (a displacement, not a
    family that was already dominant when sequencing began).
    """
    found = []
    for (name, family), group in shares.groupby(["covariants_name", "variant"]):
        group = group.sort_values("week").reset_index(drop=True)
        low, high = (pd.Timestamp(x) for x in EVENT_WINDOWS[family])
        for i in range(len(group)):
            week = group.loc[i, "week"]
            if group.loc[i, "variant_share"] < 100 * MAJORITY or not low <= week <= high:
                continue
            following = group.loc[i + 1 : i + 2, "variant_share"]
            earlier = group[group["week"] <= week - pd.Timedelta(weeks=WINDOW)]
            adjacent = i > 0 and (week - group.loc[i - 1, "week"]).days <= 14
            if (
                len(following)
                and following.mean() >= 100 * MAJORITY
                and len(earlier)
                and earlier["variant_share"].iloc[-1] < 100 * MAJORITY
                and adjacent
            ):
                found.append((name, family, week))
                break
    return pd.DataFrame(found, columns=["covariants_name", "variant", "event_week"])


def _weekly(daily: pd.DataFrame, value: str, starts: pd.DatetimeIndex) -> pd.Series:
    """Mean of daily values over the 7 days starting at each week start (>=4 days)."""
    out = {}
    series = daily.set_index("date")[value].dropna().sort_index()
    for start in starts:
        window = series[start : start + pd.Timedelta(days=6)]
        out[start] = window.mean() if len(window) >= 4 else np.nan
    return pd.Series(out)


def build_panel(raw: Path = RAW) -> pd.DataFrame:
    """Align variant takeovers with policy, mobility, cases and deaths."""
    owid = pd.read_csv(
        raw / "owid_covid.csv",
        usecols=["iso_code", "location", "continent", "median_age", "date",
                 "new_cases_smoothed_per_million", "new_deaths_smoothed_per_million"],
        parse_dates=["date"],
        keep_default_na=False,
        na_values=[""],
    )
    owid = owid[owid["iso_code"].str.len() == 3].copy()  # drops OWID_* aggregates
    locations = owid.drop_duplicates("iso_code").set_index("location")["iso_code"]

    oxcgrt = pd.read_csv(
        raw / "oxcgrt.csv",
        usecols=["CountryCode", "Jurisdiction", "Date", "StringencyIndex_Average"],
        dtype={"CountryCode": str, "Date": str},
        keep_default_na=False,
        na_values=[""],
    )
    oxcgrt = oxcgrt[oxcgrt["Jurisdiction"] == "NAT_TOTAL"].copy()
    oxcgrt["date"] = pd.to_datetime(oxcgrt["Date"], format="%Y%m%d")

    mobility = pd.read_csv(
        raw / "mobility.csv",
        usecols=["country", "region", "date", "workplaces"],
        parse_dates=["date"],
        keep_default_na=False,
        na_values=[""],
    )
    mobility = mobility[mobility["region"] == "Total"].copy()
    mobility["iso"] = mobility["country"].replace(NAME_FIXES).map(locations)

    shares = _variant_shares(raw / "covariants.json")
    events = _find_events(shares)
    events["iso"] = events["covariants_name"].replace(NAME_FIXES).map(locations)
    dropped = events[events["iso"].isna()]["covariants_name"].unique()
    if len(dropped):
        print(f"Skipping {len(dropped)} sequencing regions with no OWID country match")
    events = events.dropna(subset=["iso"])

    meta = owid.drop_duplicates("iso_code").set_index("iso_code")
    names = meta["location"]
    continents = meta["continent"].replace("", np.nan).fillna("Other")
    ages = meta["median_age"]
    rows = []
    for event in events.itertuples(index=False):
        starts = pd.DatetimeIndex(
            [event.event_week + pd.Timedelta(weeks=k) for k in range(-WINDOW, WINDOW + 1)]
        )
        o = owid[owid["iso_code"] == event.iso]
        x = oxcgrt[oxcgrt["CountryCode"] == event.iso]
        m = mobility[mobility["iso"] == event.iso]
        s = shares[(shares["covariants_name"] == event.covariants_name)
                   & (shares["variant"] == event.variant)].set_index("week")
        frame = pd.DataFrame({
            "date": starts,
            "country_code": event.iso,
            "country": names[event.iso],
            "continent": continents[event.iso],
            "median_age": ages[event.iso],
            "variant": event.variant,
            "event_week": event.event_week,
            "rel_week": range(-WINDOW, WINDOW + 1),
            "variant_share": s["variant_share"].reindex(starts).to_numpy(),
            "sequences": s["sequences"].reindex(starts).to_numpy(),
            "stringency_index": _weekly(x, "StringencyIndex_Average", starts).to_numpy(),
            "cases_per_million": _weekly(o, "new_cases_smoothed_per_million", starts).to_numpy(),
            "deaths_per_million": _weekly(o, "new_deaths_smoothed_per_million", starts).to_numpy(),
            "workplace_mobility": _weekly(m, "workplaces", starts).to_numpy(),
        })
        rows.append(frame)
    panel = pd.concat(rows, ignore_index=True)
    # keep only events with usable policy AND case data around the takeover
    usable = panel.groupby(["country_code", "variant"]).apply(
        lambda g: g["stringency_index"].notna().sum() >= 12 and g["cases_per_million"].notna().sum() >= 12,
        include_groups=False,
    )
    keep = usable[usable].index
    panel = panel.set_index(["country_code", "variant"]).loc[keep].reset_index()
    return _tidy_panel(panel)


def _tidy_panel(panel: pd.DataFrame) -> pd.DataFrame:
    panel = panel.copy()
    for column in ("date", "event_week"):
        panel[column] = pd.to_datetime(panel[column]).dt.strftime("%Y-%m-%d")
    panel["sequences"] = panel["sequences"].round().astype("Int64")
    panel["rel_week"] = panel["rel_week"].astype(int)
    panel["median_age"] = panel["median_age"].astype(float).round(1)
    for column in ("variant_share", "stringency_index", "cases_per_million",
                   "deaths_per_million", "workplace_mobility"):
        panel[column] = panel[column].astype(float).round(3)
    return (panel[PANEL_COLUMNS]
            .sort_values(["variant", "country", "rel_week"])
            .reset_index(drop=True))


def _first_week(frame: pd.DataFrame, mask: pd.Series) -> float:
    hits = frame.loc[mask & (frame["rel_week"] >= -WINDOW // 2), "rel_week"]
    return float(hits.min()) if len(hits) else np.nan


def summarise(panel: pd.DataFrame) -> pd.DataFrame:
    """One row per country x variant event: timing of tightening vs case rise."""
    rows = []
    low, high = BASELINE_WEEKS
    for (code, variant), g in panel.groupby(["country_code", "variant"]):
        g = g.sort_values("rel_week")
        base = g[g["rel_week"].between(low, high)]
        base_s, base_c = base["stringency_index"].mean(), base["cases_per_million"].mean()
        if np.isnan(base_s) or np.isnan(base_c):
            continue
        policy = _first_week(g, g["stringency_index"] >= base_s + STRINGENCY_RISE)
        threshold = max(base_c * CASE_RISE_RATIO, CASE_RISE_FLOOR)
        cases = _first_week(g, g["cases_per_million"] >= threshold)
        post = g[g["rel_week"] >= 0]
        peak = float(post.loc[post["cases_per_million"].idxmax(), "rel_week"]) if post["cases_per_million"].notna().any() else np.nan
        if not np.isnan(policy) and not np.isnan(cases):
            diff = policy - cases
            label = SEQUENCE_LABELS[0] if diff < 0 else SEQUENCE_LABELS[1] if diff > 0 else SEQUENCE_LABELS[2]
        elif not np.isnan(policy):
            diff, label = np.nan, SEQUENCE_LABELS[3]
        elif not np.isnan(cases):
            diff, label = np.nan, SEQUENCE_LABELS[4]
        else:
            diff, label = np.nan, SEQUENCE_LABELS[5]
        peak_value = post["cases_per_million"].max() if post["cases_per_million"].notna().any() else np.nan
        rows.append({
            "country_code": code,
            "country": g["country"].iloc[0],
            "continent": g["continent"].iloc[0],
            "median_age": g["median_age"].iloc[0],
            "variant": variant,
            "event_week": g["event_week"].iloc[0],
            "baseline_stringency": round(base_s, 3),
            "baseline_cases_per_million": round(base_c, 3),
            "policy_week": policy,
            "cases_week": cases,
            "policy_minus_cases": diff,
            "sequence": label,
            "peak_cases_week": peak,
            "peak_growth": round(float(peak_value / base_c), 2) if base_c > 0 and not np.isnan(peak_value) else np.nan,
        })
    out = pd.DataFrame(rows, columns=SUMMARY_COLUMNS)
    for column in ("policy_week", "cases_week", "policy_minus_cases", "peak_cases_week"):
        out[column] = out[column].astype("Int64")
    return out.sort_values(["variant", "country"]).reset_index(drop=True)


# ================================ validation ================================
def validate_panel(frame: pd.DataFrame) -> None:
    """Stop the pipeline if the panel breaks a documented expectation."""
    missing = set(PANEL_COLUMNS).difference(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if len(frame) < 100:
        raise ValueError("The panel must contain at least 100 rows")
    key = ["country_code", "variant", "rel_week"]
    if frame.duplicated(key).any():
        raise ValueError(f"Duplicate keys found for {key}")
    required = ["date", "country_code", "country", "variant", "event_week", "rel_week"]
    if frame[required].isna().any().any():
        raise ValueError("Missing values in identifier or time columns")
    if not set(frame["variant"]).issubset(VARIANTS):
        raise ValueError("Unexpected variant family")
    if not frame["rel_week"].between(-WINDOW, WINDOW).all():
        raise ValueError("Relative week outside the event window")
    dates = pd.to_datetime(frame["date"], errors="raise")
    events = pd.to_datetime(frame["event_week"], errors="raise")
    if not ((dates - events).dt.days == frame["rel_week"] * 7).all():
        raise ValueError("date must equal event_week + 7 * rel_week")
    if not frame["country_code"].str.fullmatch(r"[A-Z]{3}").all():
        raise ValueError("country_code must be an ISO 3166-1 alpha-3 code")
    if frame["continent"].isna().any():
        raise ValueError("continent must not be missing (use 'Other')")
    if frame.groupby("country_code")["country"].nunique().max() != 1:
        raise ValueError("A country code maps to more than one country name")
    ranges = {
        "variant_share": (0, 100), "stringency_index": (0, 100),
        "cases_per_million": (0, 20000), "deaths_per_million": (0, 500),
        "workplace_mobility": (-100, 200),
    }
    for column, (low, high) in ranges.items():
        values = pd.to_numeric(frame[column], errors="raise").dropna()
        if not values.between(low, high).all():
            raise ValueError(f"{column} outside the plausible range {low} to {high}")
    if (frame["sequences"].dropna() < MIN_SEQUENCES).any():
        raise ValueError(f"sequences below the minimum of {MIN_SEQUENCES}")
    around_zero = frame.loc[frame["rel_week"] == 0, "variant_share"]
    if around_zero.notna().any() and (around_zero.dropna() < 100 * MAJORITY).any():
        raise ValueError("A takeover week must have a variant share of at least 50%")


def validate_summary(frame: pd.DataFrame) -> None:
    missing = set(SUMMARY_COLUMNS).difference(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if frame.duplicated(["country_code", "variant"]).any():
        raise ValueError("Duplicate country and variant keys found")
    if frame[["country_code", "country", "variant", "event_week", "sequence"]].isna().any().any():
        raise ValueError("Missing values in identifier columns")
    if not set(frame["sequence"]).issubset(SEQUENCE_LABELS):
        raise ValueError("Unexpected sequence label")
    both = frame["policy_week"].notna() & frame["cases_week"].notna()
    if not (frame.loc[both, "policy_minus_cases"] == frame.loc[both, "policy_week"] - frame.loc[both, "cases_week"]).all():
        raise ValueError("policy_minus_cases must equal policy_week - cases_week")
    for column in ("policy_week", "cases_week", "peak_cases_week"):
        values = frame[column].dropna()
        if not values.between(-WINDOW // 2, WINDOW).all():
            raise ValueError(f"{column} outside the searched window")
    if not frame["baseline_stringency"].between(0, 100).all():
        raise ValueError("baseline_stringency outside 0 to 100")
    if not frame["baseline_cases_per_million"].between(0, 20000).all():
        raise ValueError("baseline_cases_per_million outside the plausible range")
    if frame["continent"].isna().any():
        raise ValueError("continent must not be missing (use 'Other')")
    if not frame["median_age"].dropna().between(10, 60).all():
        raise ValueError("median_age outside the plausible range")
    if (frame["peak_growth"].dropna() < 0).any():
        raise ValueError("peak_growth must not be negative")


# ================================== sample ==================================
SAMPLE_COUNTRIES = [
    "United States", "United Kingdom", "Germany", "France", "Italy", "Spain",
    "Japan", "South Korea", "Australia", "New Zealand", "Brazil", "India",
    "South Africa", "Canada", "Denmark", "Singapore", "Laos", "Mexico", "Poland",
    "Thailand", "Greece", "Nigeria", "Malaysia", "Israel", "Sweden",
]


def make_sample() -> None:
    """Cut the bundled offline sample from the full processed panel."""
    panel = pd.read_csv(PROCESSED_PANEL, keep_default_na=False, na_values=[""],
                        dtype={"country_code": str, "sequences": "Int64"})
    sample = panel[panel["country"].isin(SAMPLE_COUNTRIES)]
    sample.to_csv(SAMPLE_PANEL, index=False)
    summarise(sample).to_csv(SAMPLE_SUMMARY, index=False)
    print(f"Wrote {len(sample)} sample rows for {sample['country'].nunique()} countries")


# =================================== main ===================================
def read_panel(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"country_code": str, "sequences": "Int64"},
                       keep_default_na=False, na_values=[""])


def read_summary(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"country_code": str, "policy_week": "Int64",
                                    "cases_week": "Int64", "policy_minus_cases": "Int64",
                                    "peak_cases_week": "Int64"},
                       keep_default_na=False, na_values=[""])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquire", action="store_true", help="Download raw files and stop")
    parser.add_argument("--validate", action="store_true", help="Validate processed files and stop")
    parser.add_argument("--make-sample", action="store_true", help="Cut data/sample*.csv from processed data")
    args = parser.parse_args()
    sample_mode = os.getenv("DASHBOARD_SAMPLE_MODE", "0") == "1"

    if args.acquire:
        if sample_mode:
            parser.error("Unset DASHBOARD_SAMPLE_MODE before acquiring live data")
        acquire()
        return
    if args.validate:
        validate_panel(read_panel(PROCESSED_PANEL))
        validate_summary(read_summary(PROCESSED_SUMMARY))
        print("Processed data valid")
        return
    if args.make_sample:
        make_sample()
        return

    if sample_mode:
        panel = read_panel(SAMPLE_PANEL)
        validate_panel(panel)
        sample_summary = read_summary(SAMPLE_SUMMARY)
        validate_summary(sample_summary)
    else:
        if not RAW.exists():
            acquire()
        panel = build_panel(RAW)
        validate_panel(panel)
    summary = summarise(panel)
    validate_summary(summary)
    if sample_mode:
        pd.testing.assert_frame_equal(
            summary.reset_index(drop=True),
            read_summary(SAMPLE_SUMMARY).reset_index(drop=True),
            check_dtype=False,
            obj="derived summary vs data/sample_summary.csv",
        )
    panel = panel.sort_values(["variant", "country", "rel_week"]).reset_index(drop=True)
    PROCESSED_PANEL.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(PROCESSED_PANEL, index=False)
    summary.to_csv(PROCESSED_SUMMARY, index=False)
    print(f"Validated and wrote {len(panel)} panel rows to {PROCESSED_PANEL}")
    print(f"Validated and wrote {len(summary)} event rows to {PROCESSED_SUMMARY}")


if __name__ == "__main__":
    main()

"""The four principal views. Each render_* function draws inside the container that
the q*_page.py file opens (key = view id). Filtering happens here so the exported CSV holds
exactly the records the charts summarise."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src import charts, ui
from src.data import INCOMES, INDICATORS, NAME, REGIONS
from src.load import get_obs, records

CODES = [c for c, *_ in INDICATORS]
SHORT = [n for _, n, *_ in INDICATORS]
LAW_CODE = "SG.LAW.INDX"
BY_NAME = {n: c for c, n in NAME.items()}
OUTCOMES = ["Women in the labour force", "Labour force: women and men", "Girls in secondary school",
            "Women in parliament", "Women with an account"]
RANKABLE = ["Women in the labour force", "Girls in secondary school", "Women in parliament", "Women with an account"]
YEAR_END = 2025   # last year of observations in the data set

TITLES = {
    "what_can_we_see": "What can we actually see?",
    "law_vs_outcomes": "Do laws change faster than outcomes?",
    "law_vs_reality": "Where do law and reality seem out of step?",
    "evidence_breaks": "Where does the evidence break off?",
}
UNITS = {
    "what_can_we_see": "year of the latest value; years behind the newest year found for that indicator in the database",
    "law_vs_outcomes": "law score 0 to 100 (WBL 1.0 points rescaled); outcomes in percent",
    "law_vs_reality": "rank among countries with both values (1 is highest); law score 0 to 100; outcomes in percent",
    "evidence_breaks": "calendar years with a recorded value, 2000 to 2025",
}


def found(text: str) -> None:
    st.markdown(f'<div class="found">{text}</div>', unsafe_allow_html=True)


def heading(key: str, number: int) -> None:
    st.markdown(f'<div class="eyebrow">Question {number}</div>', unsafe_allow_html=True)
    st.subheader(TITLES[key])


def footer(key: str, csv: pd.DataFrame, name: str, extra: str | None = None) -> None:
    st.caption(f"Unit: {UNITS[key]}")
    if extra:
        st.caption(extra)
    ui.attribution(ui.ALL_SOURCES)
    ui.latest_caption(get_obs()["date"].max())   # the newest observation date in the data set
    ui.download(csv, f"{key}_download", name)


def clean_state(key: str, options: list) -> None:
    """Drop a stored selection that is no longer among the options (Streamlit would raise)."""
    if key in st.session_state and st.session_state[key] not in options:
        del st.session_state[key]


# --------------------------------------------------------------- Q1 --------
def seed_geo(prefix: str) -> None:
    ui.seed(f"{prefix}_region", list(REGIONS))
    ui.seed(f"{prefix}_income", list(INCOMES))


def geo_filters(prefix: str) -> tuple[list[str], list[str]]:
    regions = st.multiselect("Region", REGIONS, key=f"{prefix}_region")
    incomes = st.multiselect("Income group", INCOMES, key=f"{prefix}_income")
    return regions, incomes


def open_in_q4() -> None:
    ss = st.session_state
    ss["q4_handoff"] = ([ss["q1_inv_country"]], [ss["q1_inv_indicator"]])   # read by Question 4 on arrival


def render_what_can_we_see(status: pd.DataFrame) -> None:
    key = "what_can_we_see"
    seed_geo("q1")
    ui.seed("q1_find", "")
    ui.seed("q1_sort", "Most gaps first")
    ui.seed("q1_rows", "30 countries")
    head = st.container()
    body = st.container()
    with body:
        c1, c2 = st.columns(2)
        find = c1.text_input("Find a country (starts with a capital, e.g. Ken)", key="q1_find")
        sort = c2.selectbox("Sort countries by", ["Most gaps first", "Oldest data first", "Name", "Region"], key="q1_sort")
        rows_n = st.selectbox("Rows drawn", ["30 countries", "60 countries", "All countries in the selection"], key="q1_rows")
        with st.expander("More filters"):
            regions, incomes = geo_filters("q1")
        f = status[status["region"].isin(regions) & status["income_group"].isin(incomes)]
        if find:
            f = f[f["country"].str.contains(find, case=True, regex=False)]
        csv = f
        if f.empty:
            st.info(ui.EMPTY_MESSAGE)
        else:
            per = f.groupby(["country_code", "country", "region"]).agg(
                gaps=("status", lambda s: int((s == "No value in WDI").sum())),
                old=("status", lambda s: int((s == "Behind").sum())),
                worst=("years_behind", lambda s: int(s.max()) if s.notna().any() else 0)).reset_index()
            n = len(per)
            all_six = int((per["gaps"] == 0).sum())
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Countries in the selection", n)
            m2.metric("With a value for all six", all_six)
            m3.metric("Missing at least one", int((per["gaps"] > 0).sum()))
            m4.metric("With an old value", int((per["old"] > 0).sum()))
            sorter = {"Most gaps first": (["gaps", "old", "country"], [False, False, True]),
                      "Oldest data first": (["worst", "gaps", "country"], [False, False, True]),
                      "Name": (["country"], [True]), "Region": (["region", "country"], [True, True])}[sort]
            shown = per.sort_values(sorter[0], ascending=sorter[1])
            limit = {"30 countries": 30, "60 countries": 60}.get(rows_n, len(shown))
            shown = shown.head(limit)
            if shown.empty:
                st.info("Every country in this selection has all six indicators up to date.")
            else:
                ui.legend((charts.FG, "Latest value is the newest in the database"), ("#9fb0c8", "older"),
                          (charts.PALE, "14 or more years behind"), (charts.MISS, "no value in WDI"))
                sub = f[f["country_code"].isin(shown["country_code"])]
                rows = records(sub.assign(c=sub["country"], i=sub["indicator"], yr=sub["latest_year"].astype("Int64").astype(str)
                                          .replace("<NA>", ""), b=sub["years_behind"], s=sub["status"], v=sub["latest_value"])
                               [["c", "i", "yr", "b", "s", "v"]])
                charts.show(charts.matrix(rows, list(shown["country"]), SHORT))
                if len(per) > len(shown):
                    st.caption(f"Showing {len(shown)} of {len(per)} countries in the selection. The table and the download cover all of them.")
            summary = (f.groupby("indicator_code").agg(
                have=("latest_year", lambda s: int(s.notna().sum())),
                behind=("status", lambda s: int((s == "Behind").sum())),
                median_lag=("years_behind", lambda s: float(s.median()) if s.notna().any() else np.nan),
                newest=("newest_year_in_wdi", "first")).reindex(CODES))
            table = pd.DataFrame({
                "Indicator": SHORT,
                "Countries with a value": [f"{h} of {n}" for h in summary["have"]],
                "Coverage (%)": (summary["have"] / n * 100).round(0).astype(int).to_numpy(),
                "Values past the threshold": summary["behind"].astype(int).to_numpy(),
                "Median years behind": summary["median_lag"].round(1).to_numpy(),
                "Newest year in WDI": summary["newest"].astype(int).to_numpy()})
            st.dataframe(table, hide_index=True, width="stretch")
            st.markdown('<div class="eyebrow">Investigate a gap</div>', unsafe_allow_html=True)
            names = list(shown["country"]) if len(shown) else list(per["country"])
            clean_state("q1_inv_country", names)
            i1, i2, i3 = st.columns([1.3, 1.3, 1])
            i1.selectbox("Country", names, key="q1_inv_country")
            i2.selectbox("Indicator", SHORT, key="q1_inv_indicator")
            if i3.button("Open in Question 4", key="q1_open_q4"):
                open_in_q4()
                st.switch_page("q4_page.py")
            st.caption("Opens the year-by-year grid in Question 4 for that country and indicator.")
    with head:
        heading(key, 1)
        if not f.empty:
            worst = table.assign(h=summary["have"].to_numpy()).sort_values("h").iloc[0]
            found(f"Of {n} countries, {all_six} have a value for all six indicators. The thinnest indicator is "
                  f"<b>{worst['Indicator']}</b>, with a value for {worst['Countries with a value']} countries.")
    footer(key, csv, "what_can_we_see.csv",
           "Past the threshold: more than 4 years behind the newest year for that indicator (6 years for the account survey, "
           "which runs about every three years). Coverage counts countries with any value, however old.")


# --------------------------------------------------------------- Q2 --------
def seg_ids(years: list[int]) -> list[int]:
    seg, out, prev = 0, [], None
    for y in years:
        if prev is not None and y - prev > 1:
            seg += 1
        out.append(seg)
        prev = y
    return out


def render_law_vs_outcomes(obs: pd.DataFrame) -> None:
    key = "law_vs_outcomes"
    countries_all = sorted(obs["country"].unique())
    ui.seed("q2_countries", ["Kenya"])
    ui.seed("q2_outcome", "Women in the labour force")
    head = st.container()
    body = st.container()
    with body:
        c1, c2 = st.columns([1.4, 1])
        chosen = c1.multiselect("Countries (up to three)", countries_all, key="q2_countries", max_selections=3)
        outcome = c2.selectbox("Outcome indicator", OUTCOMES, key="q2_outcome")
        f = obs[obs["country"].isin(chosen)]
        csv = f
        if f.empty:
            st.info(ui.EMPTY_MESSAGE)
        else:
            codes = {"Labour force: women and men": ["SL.TLF.CACT.FE.ZS", "SL.TLF.CACT.MA.ZS"]}.get(
                outcome, [BY_NAME[outcome]])
            series = f[f["indicator_code"].isin([LAW_CODE] + codes)].sort_values(["country", "indicator_code", "year"])
            law_title = "Law score (0 to 100)"
            out_title = {"Labour force: women and men": "Labour force participation, women and men (%)"}.get(
                outcome, f"{outcome} (%)")
            rows = []
            for (country, code), g in series.groupby(["country", "indicator_code"]):
                ids = seg_ids(list(g["year"]))
                label = NAME[code] if code != LAW_CODE else "Law score"
                for (_, r), s in zip(g.iterrows(), ids):
                    rows.append({"c": country, "series": label, "yr": int(r["year"]), "v": float(r["value"]),
                                 "grp": f"{country}|{code}|{s}",
                                 "panel": law_title if code == LAW_CODE else out_title})
            has_law = any(r["panel"] == law_title for r in rows)
            has_out = any(r["panel"] == out_title for r in rows)
            first = chosen[0] if chosen else None
            fl = series[(series["country"] == first)]
            m1, m2, m3 = st.columns(3)
            lawf = fl[fl["indicator_code"] == LAW_CODE]
            outf = fl[fl["indicator_code"] == codes[0]]
            m1.metric(f"{first}: law score, latest",
                      f"{lawf['value'].iloc[-1]:.1f} ({lawf['year'].iloc[-1]})" if len(lawf) else "none recorded")
            m2.metric(f"{first}: {codes and NAME[codes[0]].lower()}, latest",
                      f"{outf['value'].iloc[-1]:.1f}% ({outf['year'].iloc[-1]})" if len(outf) else "none recorded")
            m3.metric("Years with an outcome value", int(outf["year"].nunique()))
            if not has_out:
                st.info("No value for this outcome in the selected countries.")
            elif not has_law:
                st.info("No law score for the selected countries. Only the outcome is drawn.")
            if has_out or has_law:
                charts.show(charts.trend(rows, chosen, has_law, out_title, outcome == "Labour force: women and men"))
    with head:
        heading(key, 2)
        st.caption("Dashed lines mark 2020 and 2022, where the law score's question set changed. Scores across them are not strictly comparable.")
        if not f.empty and first:
            bits = []
            if len(lawf) > 1:
                bits.append(f"the law score went from {lawf['value'].iloc[0]:.1f} in {lawf['year'].iloc[0]} to "
                            f"{lawf['value'].iloc[-1]:.1f} in {lawf['year'].iloc[-1]}")
            if len(outf) > 1:
                bits.append(f"{NAME[codes[0]].lower()} went from {outf['value'].iloc[0]:.1f}% in {outf['year'].iloc[0]} to "
                            f"{outf['value'].iloc[-1]:.1f}% in {outf['year'].iloc[-1]}")
            if bits:
                found(f"In {first}, " + ", and ".join(bits) + ".")
            else:
                found(f"{first} has too few years to compare a trend.")
    footer(key, csv, "law_vs_outcomes.csv")


# --------------------------------------------------------------- Q3 --------
def ranked(f: pd.DataFrame, outcome: str) -> pd.DataFrame:
    law = f[f["indicator_code"] == LAW_CODE][["country_code", "country", "latest_value", "latest_year"]]
    out = f[f["indicator_code"] == BY_NAME[outcome]][["country_code", "latest_value", "latest_year"]]
    both = law.merge(out, on="country_code", suffixes=("_law", "_out")).dropna()
    both["law_rank"] = both["latest_value_law"].rank(ascending=False, method="min").astype(int)
    both["out_rank"] = both["latest_value_out"].rank(ascending=False, method="min").astype(int)
    return both


def render_law_vs_reality(status: pd.DataFrame) -> None:
    key = "law_vs_reality"
    seed_geo("q3")
    ui.seed("q3_outcome", "Women in the labour force")
    ui.seed("q3_direction", "Law ranks better than the outcome")
    head = st.container()
    body = st.container()
    with body:
        c1, c2 = st.columns(2)
        outcome = c1.selectbox("Outcome indicator", RANKABLE, key="q3_outcome")
        direction = c2.radio("Show", ["Law ranks better than the outcome", "Outcome ranks better than law"], key="q3_direction")
        with st.expander("More filters"):
            regions, incomes = geo_filters("q3")
        f = status[status["region"].isin(regions) & status["income_group"].isin(incomes)]
        csv = f
        if f.empty:
            st.info(ui.EMPTY_MESSAGE)
        else:
            both = ranked(f, outcome)
            n = len(both)
            law_dir = direction.startswith("Law")
            both["gap"] = both["out_rank"] - both["law_rank"] if law_dir else both["law_rank"] - both["out_rank"]
            top = both[both["gap"] > 0].sort_values(["gap", "country"], ascending=[False, True]).head(15)
            m1, m2, m3 = st.columns(3)
            m1.metric("Countries with both values", n)
            m2.metric("Left out (one value missing)", int(f["country_code"].nunique() - n))
            m3.metric("Largest gap, in places", int(top["gap"].iloc[0]) if len(top) else 0)
            if n < 5:
                st.info("Fewer than five countries have both values, so ranks are not shown.")
            elif top.empty:
                st.info("No country ranks better in this direction in the current selection.")
            else:
                ui.legend((charts.LAW if law_dir else charts.OUT, "Gap between the two ranks, in places"))
                rows = [{"c": r.country, "gap": int(r.gap), "lr": int(r.law_rank), "or": int(r.out_rank), "of": n,
                         "lv": float(r.latest_value_law), "ly": int(r.latest_year_law),
                         "ov": float(r.latest_value_out), "oy": int(r.latest_year_out)} for r in top.itertuples()]
                charts.show(charts.rank_bars(rows, law_dir, outcome))
                detail = top.rename(columns={"country": "Country", "law_rank": "Law rank", "out_rank": "Outcome rank",
                                             "latest_value_law": "Law score", "latest_year_law": "Law year",
                                             "latest_value_out": outcome, "latest_year_out": "Outcome year"})
                st.dataframe(detail[["Country", "Law rank", "Outcome rank", "Law score", "Law year", outcome, "Outcome year"]]
                             .assign(**{"Law score": detail["Law score"].round(1), outcome: detail[outcome].round(1)}),
                             hide_index=True, width="stretch")
    with head:
        heading(key, 3)
        if not f.empty and n >= 5 and not top.empty:
            found(f"Among {n} countries with both values, <b>{top.iloc[0]['country']}</b> shows the widest gap "
                  f"({int(top.iloc[0]['gap'])} places), with law rank {int(top.iloc[0]['law_rank'])} and "
                  f"{outcome.lower()} rank {int(top.iloc[0]['out_rank'])}.")
    footer(key, csv, "law_vs_reality.csv",
           "The download holds every indicator for the countries in the selection, not only the ranked pair.")


# --------------------------------------------------------------- Q4 --------
def render_evidence_breaks(obs: pd.DataFrame, status: pd.DataFrame) -> None:
    key = "evidence_breaks"
    countries_all = sorted(obs["country"].unique())
    ui.seed("q4_countries", ["Afghanistan", "Brazil", "India", "Nigeria", "Somalia, Fed. Rep.", "Yemen, Rep."])
    ui.seed("q4_indicators", list(SHORT))
    ui.seed("q4_from", 2000)
    handoff = st.session_state.pop("q4_handoff", None)
    if handoff:
        st.session_state["q4_indicators"] = handoff[1]
        # A country with no observation at all is not an option in this view; keep the current countries then.
        st.session_state["q4_countries"] = [c for c in handoff[0] if c in countries_all] or st.session_state["q4_countries"]
    head = st.container()
    body = st.container()
    with body:
        chosen = st.multiselect("Countries", countries_all, key="q4_countries")
        c1, c2 = st.columns([2, 1])
        inds = c1.multiselect("Indicators", SHORT, key="q4_indicators")
        start = c2.selectbox("First year shown", [2000, 2005, 2010, 2015], key="q4_from")
        f = obs[obs["country"].isin(chosen) & obs["indicator"].isin(inds)]
        csv = f
        if f.empty:
            st.info(ui.EMPTY_MESSAGE)
        else:
            years = list(range(start, YEAR_END + 1))
            have = {(r.country, r.indicator, r.year) for r in f.itertuples()}
            last = status.set_index(["country", "indicator"])
            order, rows, gaps, ended, never = [], [], 0, 0, 0
            for country in sorted(chosen):
                for ind in [i for i in SHORT if i in inds]:
                    st_row = last.loc[(country, ind)]
                    ly = st_row["latest_year"]
                    tag = "never recorded" if pd.isna(ly) else f"last {int(ly)}"
                    label = f"{country} · {ind} · {tag}"
                    order.append(label)
                    never += int(pd.isna(ly))
                    ended += int(st_row["status"] == "Behind")
                    kind = "Law score" if ind == SHORT[0] else "Outcome"
                    for y in years:
                        rows.append({"r": label, "yr": y, "has": int((country, ind, y) in have), "k": kind})
            m1, m2, m3 = st.columns(3)
            m1.metric("Rows (country and indicator)", len(order))
            m2.metric("Never recorded", never)
            m3.metric("Ending well behind", ended)
            charts.show(charts.year_grid(rows, order, years))
            st.caption("Rows are sorted by country. A filled square means a value was recorded that year. "
                       "The label gives the latest year in the whole database, even if it is before the first year shown.")
    with head:
        heading(key, 4)
        ui.legend((charts.LAW, "Law score"), (charts.OUT, "Outcome"), (charts.PALE, "No value that year"))
        if not f.empty:
            found(f"Of {len(order)} country and indicator rows here, {never} have no value at all and {ended} end "
                  f"further behind the newest year than the indicator's threshold allows.")
    footer(key, csv, "evidence_breaks.csv")

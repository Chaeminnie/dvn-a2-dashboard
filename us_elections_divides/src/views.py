"""The four principal views. Each render_* function draws inside the container that the q*_page.py
file opens (key = view id). Filtering happens here so the exported CSV holds exactly the records the charts
summarise: the rows of the dataset that match the view's filters."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src import charts, ui
from src.data import ELECTION_DAY, ELECTION_TYPE, KEYWORDS, SMALL_STATE_VOTES

FACTORS = ["Gender", "Income", "Region"]
SHIFT_LIMIT, MARGIN_LIMIT = 12, 40   # colour scale ends (percentage points); the caption under the tile map reads from these
PAIRS = {"Gender": ("Women", "Men"), "Income": ("Low", "High"), "Region": ("Northeast", "South")}
DISPLAY = {"Low": "Lower income", "High": "Higher income"}
AGE4 = ["18-29", "30-44", "45-64", "65+"]
AGE_ALL = ["All ages"] + AGE4
ELECTIONS = [2024, 2022, 2020, 2018, 2016]
SHIFT_ELECTIONS = [2024, 2020]
REGIONS = ["Northeast", "Midwest", "South", "West"]
KEY = {"q1": "who_divides_voters", "q2": "state_shift", "q3": "phrase_and_gap", "q4": "search_by_state"}

TITLES = {
    "who_divides_voters": "What divides voters most?",
    "state_shift": "How did states move between elections?",
    "phrase_and_gap": "Did the gap change after a phrase took off?",
    "search_by_state": "Did states that searched more move differently?",
}
UNITS = {
    "who_divides_voters": "percentage points of the two-party vote (size of the divide, direction); percent of validated voters (turnout)",
    "state_shift": "change in the Democratic minus Republican margin, percentage points of the two-party vote",
    "phrase_and_gap": "search interest index (0 to 100, relative to each phrase's own peak); size of the gap in percentage points of the two-party vote",
    "search_by_state": "search interest index (0 to 100, by state); change in margin, 2020 to 2024, percentage points of the two-party vote",
}
LATEST = {"who_divides_voters": "2024-11-05", "state_shift": "2024-11-05", "phrase_and_gap": "2026-09-01",
          "search_by_state": "2024-11-04"}


def name_of(g: str) -> str:
    return DISPLAY.get(g, g)


def heading(key: str, number: int) -> None:
    st.markdown(f'<div class="eyebrow">Question {number}</div>', unsafe_allow_html=True)
    st.subheader(TITLES[key])


def footer(key: str, csv: pd.DataFrame, name: str, source_ids: list[str], extra: str | None = None) -> None:
    st.caption(f"Unit: {UNITS[key]}")
    if extra:
        st.caption(extra)
    ui.attribution(source_ids)
    ui.latest_caption(LATEST[key])
    ui.download(csv, f"{key}_download", name)


def election_label(year: int) -> str:
    return f"{year} {ELECTION_TYPE[year][0]}"


def cell_lookup(frame: pd.DataFrame) -> dict:
    return {(r.factor, r.group, r.age_band): r for r in frame.itertuples(index=False)}


def gap_rows(f: pd.DataFrame, highlight: str) -> list[dict]:
    """One row per split (factor) and age band for a single election."""
    look = cell_lookup(f)
    out = []
    for factor in FACTORS:
        a_name, b_name = PAIRS[factor]
        for age in AGE4:
            a, b = look[(factor, a_name, age)], look[(factor, b_name, age)]
            pa, pb = float(a.dem_share_pct), float(b.dem_share_pct)
            out.append({"r": f"{factor} · {age}", "factor": factor, "age": age, "a": name_of(a_name), "b": name_of(b_name),
                        "pa": pa, "pb": pb, "lo": min(pa, pb), "hi": max(pa, pb), "gap": abs(pa - pb),
                        "ca": ui.DEM if pa >= 50 else ui.REP, "cb": ui.DEM if pb >= 50 else ui.REP,
                        "op": 1.0 if highlight in ("None", age) else 0.4, "n": int(min(a.n_two_party, b.n_two_party))})
    return out


# --------------------------------------------------------------- Q1 --------
def render_who_divides(voters: pd.DataFrame) -> None:
    key = KEY["q1"]
    ui.seed("q1_election", 2024)
    ui.seed("q1_view", "Dot plot")
    ui.seed("q1_mode", "Size of the divide")
    ui.seed("q1_age", "18-29")
    all_gaps = []
    for e in ELECTIONS:
        all_gaps += [r["gap"] for r in gap_rows(voters[voters["election_year"] == e], "None")]
    gap_max = float(np.ceil(max(all_gaps) / 5) * 5)
    head = st.container()
    body = st.container()
    with body:
        c1, c2 = st.columns([1, 1.6])
        election = c1.selectbox("Election", ELECTIONS, key="q1_election")
        view = c2.radio("Chart", ["Dot plot", "Heatmap", "Over time"], key="q1_view", horizontal=True)
        c3, c4 = st.columns([1.6, 1])
        mode = c3.radio("Show", ["Size of the divide", "Who leans which way"], key="q1_mode", horizontal=True)
        age = c4.selectbox("Highlight an age band", ["None"] + AGE4, key="q1_age")
        f = voters[voters["election_year"] == election]
        csv = f
        rows = gap_rows(f, age)
        order = [r["r"] for r in rows]
        et = ELECTION_TYPE[election]
        vote_for = "the presidential vote" if et == "Presidential" else "the vote for the U.S. House"
        st.caption(f"{election} {et.lower()} election. Survey answers about {vote_for}. Two-party vote only.")
        if view == "Dot plot" and mode == "Who leans which way":
            ui.legend((ui.DEM, "Leans Democratic"), (ui.REP, "Leans Republican"),
                      (ui.MUT, "Filled dot: Women, Lower income, Northeast. Hollow dot: Men, Higher income, South"))
            charts.show(charts.dot_plot(rows, order, size_mode=False, domain=(25, 80)))
        elif view == "Dot plot":
            ui.legend((ui.AMBER, "Gap between the two groups in a row (Women vs Men, Lower vs Higher income, Northeast vs South)"))
            charts.show(charts.dot_plot(rows, order, size_mode=True, domain=(0, gap_max)))
        elif view == "Heatmap":
            heat = []
            for r in rows:
                fill, ink = ui.size_fill(r["gap"] / gap_max)
                heat.append({"col": r["factor"], "row": r["age"], "v": f"{r['gap']:.1f} pp", "fill": fill, "ink": ink,
                             "sel": 1 if r["age"] == age else 0, "tip": f"{r['gap']:.1f} pp ({r['a']} {r['pa']:.1f}% vs {r['b']} {r['pb']:.1f}%)"})
            ui.ramp_legend([ui.RAMP0, ui.AMBER], "0 pp", f"{gap_max:.0f} pp or more")
            charts.show(charts.heat(heat, FACTORS, AGE4))
        else:
            heat = []
            for e in ELECTIONS:
                for r in gap_rows(voters[voters["election_year"] == e], age):
                    fill, ink = ui.size_fill(r["gap"] / gap_max)
                    heat.append({"col": election_label(e), "row": r["r"], "v": f"{r['gap']:.0f}", "fill": fill, "ink": ink,
                                 "sel": 1 if e == election else 0, "tip": f"{r['gap']:.1f} pp"})
            ui.ramp_legend([ui.RAMP0, ui.AMBER], "0 pp", f"{gap_max:.0f} pp or more")
            charts.show(charts.heat(heat, [election_label(e) for e in sorted(ELECTIONS)], order))
        big = max(rows, key=lambda r: r["gap"])
        small = min(rows, key=lambda r: r["gap"])
        m1, m2, m3 = st.columns(3)
        m1.metric("Largest gap", f"{big['gap']:.1f} pp")
        m2.metric("Median gap", f"{float(np.median([r['gap'] for r in rows])):.1f} pp")
        m3.metric("Smallest gap", f"{small['gap']:.1f} pp")
        look = cell_lookup(f)
        turn_age = "All ages" if age == "None" else age
        parts = []
        for factor in FACTORS:
            for g in PAIRS[factor]:
                parts.append(f"{name_of(g)} <b>{look[(factor, g, turn_age)].validated_turnout_pct:.0f}%</b>")
        st.markdown(f'<div class="turn">Turnout among validated voters, ages {turn_age}, shown on its own: ' + " · ".join(parts) + "</div>",
                    unsafe_allow_html=True)
    with head:
        heading(key, 1)
        ui.found(f"{election}: the biggest gap is {big['factor'].lower()} among ages {big['age']}, {big['gap']:.1f} points.")
    footer(key, csv, "who_divides_voters.csv", ["ces"])


# --------------------------------------------------------------- Q2 --------
def render_state_shift(states: pd.DataFrame) -> None:
    key = KEY["q2"]
    ui.seed("q2_election", 2024)
    ui.seed("q2_region", list(REGIONS))
    ui.seed("q2_measure", "How the margin moved")
    head = st.container()
    body = st.container()
    with body:
        c1, c2 = st.columns([1, 2])
        election = c1.selectbox("Later election", SHIFT_ELECTIONS, key="q2_election")
        measure = c2.radio("Colour by", ["How the margin moved", "Who led"], key="q2_measure", horizontal=True)
        regions = st.multiselect("Region", REGIONS, key="q2_region")
        f = states[(states["election_year"] == election) & states["region"].isin(regions)]
        csv = f
        prev = election - 4
        if f.empty:
            st.info(ui.EMPTY_MESSAGE)
        else:
            moved = measure == "How the margin moved"
            items = []
            for r in f.itertuples(index=False):
                if moved:
                    fill, ink = ui.lean_fill(r.shift_pp, SHIFT_LIMIT)
                    v, tip = ui.sgn(r.shift_pp), f"{ui.sgn(r.shift_pp)} pp ({ui.sgn(r.previous_margin_pp)} in {prev}, {ui.sgn(r.margin_pp)} in {election})"
                else:
                    fill, ink = ui.lean_fill(r.margin_pp, MARGIN_LIMIT)
                    v, tip = ui.sgn(r.margin_pp, 0), f"{ui.sgn(r.margin_pp)} pp in {election} ({r.dem_two_party_pct:.1f}% Democratic)"
                items.append({"code": r.state_code, "name": r.state, "fill": fill, "ink": ink, "v": v, "tip": tip})
            lim = f"{SHIFT_LIMIT if moved else MARGIN_LIMIT} pp each way"
            ui.ramp_legend([ui.REP, ui.MID, ui.DEM], "← Republican", "Democratic →")
            st.caption(lim)
            charts.show(charts.tiles(charts.prepare_tiles(items)))
            shifts = f["shift_pp"]
            to_r = int((shifts < 0).sum())
            m1, m2, m3 = st.columns(3)
            m1.metric("Moved toward Republican", to_r)
            m2.metric("Moved toward Democratic", int((shifts > 0).sum()))
            m3.metric("Median shift", f"{ui.sgn(shifts.median())} pp")
    with head:
        heading(key, 2)
        if not f.empty:
            low, high = f.loc[f["shift_pp"].idxmin()], f.loc[f["shift_pp"].idxmax()]
            ui.found(f"{prev} to {election}: {to_r} of {len(f)} states moved toward the Republican candidate. Biggest moves: "
                     f"{low['state']} ({ui.sgn(low['shift_pp'])} pp), {high['state']} ({ui.sgn(high['shift_pp'])} pp).")
    footer(key, csv, "state_shift.csv", ["medsl_president"])


# --------------------------------------------------------------- Q3 --------
def boom_index(values: list[int], threshold: int, rule: str) -> int:
    for i, v in enumerate(values):
        if v >= threshold and (rule == "First month" or (i + 2 < len(values) and values[i + 1] >= threshold and values[i + 2] >= threshold)):
            return i
    return -1


def render_phrase_and_gap(monthly: pd.DataFrame, voters: pd.DataFrame) -> None:
    key = KEY["q3"]
    ui.seed("q3_keyword", "tradwife")
    ui.seed("q3_factor", "Gender")
    ui.seed("q3_age", "18-29")
    ui.seed("q3_threshold", 50)
    ui.seed("q3_rule", "First month")
    st.markdown('<div class="eyebrow">Question 3</div>', unsafe_allow_html=True)
    st.subheader(TITLES[key])
    head = st.container()
    c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1, 1.4, 1.2])
    keyword = c1.selectbox("Phrase", KEYWORDS, key="q3_keyword")
    factor = c2.selectbox("Gap between", FACTORS, key="q3_factor")
    age = c3.selectbox("Age band", AGE_ALL, key="q3_age")
    threshold = c4.slider("Boom threshold (% of the phrase's peak)", 25, 75, key="q3_threshold", step=5)
    rule = c5.selectbox("Boom rule", ["First month", "3 months in a row"], key="q3_rule")
    f = monthly[monthly["keyword"] == keyword].sort_values("date")
    csv = f
    dates, vals = f["date"].tolist(), f["interest"].astype(int).tolist()
    i = boom_index(vals, threshold, rule)
    boom_date = dates[i] if i >= 0 else None
    a_name, b_name = PAIRS[factor]
    gaps = {}
    for e in ELECTIONS:
        pa = float(voters[(voters.election_year == e) & (voters.factor == factor) & (voters.group == a_name) & (voters.age_band == age)].dem_share_pct.iloc[0])
        pb = float(voters[(voters.election_year == e) & (voters.factor == factor) & (voters.group == b_name) & (voters.age_band == age)].dem_share_pct.iloc[0])
        gaps[e] = abs(pa - pb)
    before = max((e for e in ELECTIONS if boom_date and ELECTION_DAY[e] <= boom_date), default=None)
    after = min((e for e in ELECTIONS if boom_date and ELECTION_DAY[e] > boom_date), default=None)
    change = gaps[after] - gaps[before] if before and after else None
    body = st.container()
    with body:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Boom month", boom_date[:7] if boom_date else "none")
        m2.metric("Election before", election_label(before) if before else "none")
        m3.metric("Election after", election_label(after) if after else "not yet")
        m4.metric("Change in gap", f"{ui.sgn(change)} pp" if change is not None else "n/a")
        search = [{"d": d, "v": v} for d, v in zip(dates, vals)]
        elections = [{"d": ELECTION_DAY[e], "tag": election_label(e)} for e in sorted(ELECTIONS)]
        gap_points = [{"d": ELECTION_DAY[e], "g": gaps[e], "gl": f"{gaps[e]:.1f}", "tag": election_label(e),
                     "sz": 220 if e in (before, after) else 70} for e in sorted(ELECTIONS)]
        boom = None
        if boom_date:
            late = boom_date >= "2021-01-01"   # booms in the right part of the chart get their label on the left of the dot
            boom = {"d": boom_date, "v": vals[i], "align": "right" if late else "left", "dx": -10 if late else 10,
                    "label": f"{'First month' if rule == 'First month' else 'First of 3 months'} at or above {threshold}% of peak: {boom_date[:7]}"}
        title = f"Size of the gap, {factor.lower()}: {name_of(a_name)} vs {name_of(b_name)}, ages {age} (points)"
        charts.show(charts.phrase_gap(search, elections, boom, gap_points, keyword, title, float(np.ceil(max(gaps.values()) / 5) * 5 + 2)))
    with head:
        if change is None:
            ui.found(f"{keyword}: " + ("interest never reached this threshold." if not boom_date else
                                       "there is no election on both sides of the boom, so no change in the gap is shown."))
        else:
            ui.found(f"{keyword}: boom in {boom_date[:7]}. The {factor.lower()} gap, ages {age}, went from "
                     f"{gaps[before]:.1f} points in {before} to {gaps[after]:.1f} in {after}.")
    footer(key, csv, "phrase_and_gap.csv", ["google_trends", "ces"])


# --------------------------------------------------------------- Q4 --------
def render_search_by_state(shift: pd.DataFrame) -> None:
    key = KEY["q4"]
    ui.seed("q4_keyword", "tradwife")
    ui.seed("q4_region", list(REGIONS))
    ui.seed("q4_view", "Maps")
    ui.seed("q4_small", False)
    head = st.container()
    body = st.container()
    with body:
        c1, c2 = st.columns([1, 1.4])
        keyword = c1.selectbox("Phrase", KEYWORDS, key="q4_keyword")
        view = c2.radio("Chart", ["Maps", "Scatter"], key="q4_view", horizontal=True)
        regions = st.multiselect("Region", REGIONS, key="q4_region")
        small = st.checkbox(f"Leave out small states (fewer than {SMALL_STATE_VOTES:,} two-party votes in 2024)", key="q4_small")
        f = shift[(shift["keyword"] == keyword) & shift["region"].isin(regions)]
        csv = f
        plot = f[f["small_state"] == "No"] if small else f
        used = plot.dropna(subset=["interest"])
        r_val = float(np.corrcoef(used["interest"].astype(float), used["shift_2020_2024"])[0, 1]) if len(used) > 2 else float("nan")
        if f.empty or plot.empty:
            st.info(ui.EMPTY_MESSAGE)
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric("States used", len(used))
            m2.metric("Correlation (r)", "n/a" if np.isnan(r_val) else f"{r_val:.2f}")
            m3.metric("Missing search value", int(plot["interest"].isna().sum()))
            if view == "Maps":
                a, b = [], []
                for r in plot.itertuples(index=False):
                    edge = {"edge": ui.FG, "edgew": 1.3, "dash": [2, 2]} if r.small_state == "Yes" else {}
                    if pd.isna(r.interest):
                        a.append({"code": r.state_code, "name": r.state, "fill": ui.NODATA, "ink": ui.MUT, "v": "n/a", "tip": "no value in the export", **edge})
                    else:
                        fill, ink = ui.interest_fill(float(r.interest))
                        a.append({"code": r.state_code, "name": r.state, "fill": fill, "ink": ink, "v": str(int(r.interest)),
                                  "tip": f"interest {int(r.interest)} of 100", **edge})
                    fill, ink = ui.lean_fill(r.shift_2020_2024, 12)
                    b.append({"code": r.state_code, "name": r.state, "fill": fill, "ink": ink, "v": ui.sgn(r.shift_2020_2024),
                              "tip": f"margin {ui.sgn(r.shift_2020_2024)} pp", **edge})
                st.markdown(f'<div class="eyebrow">Search interest · {keyword}</div>', unsafe_allow_html=True)
                ui.ramp_legend([ui.RAMP0, ui.TEAL], "0", "100")
                charts.show(charts.tiles(charts.prepare_tiles(a), height=270))
                st.markdown('<div class="eyebrow">Margin shift, 2020 to 2024</div>', unsafe_allow_html=True)
                ui.ramp_legend([ui.REP, ui.MID, ui.DEM], "← Republican", "Democratic →")
                charts.show(charts.tiles(charts.prepare_tiles(b), height=270))
                st.caption("White outline: small state, so few searches and noisy values. Grey: no search value in the export.")
            else:
                ui.legend((ui.DEM, "Moved toward Democratic"), (ui.REP, "Moved toward Republican"))
                x = used["interest"].astype(float).to_numpy()
                y = used["shift_2020_2024"].to_numpy()
                lab = [""] * len(used)
                if len(used) > 5:
                    slope, icpt = np.polyfit(x, y, 1)
                    resid = np.abs(y - (slope * x + icpt))
                    for j in np.argsort(-resid)[:5]:
                        lab[j] = used["state_code"].iloc[j]
                rows = [{"name": n, "x": float(a_), "y": float(b_), "col": ui.DEM if b_ >= 0 else ui.REP, "lab": l}
                        for n, a_, b_, l in zip(used["state"], x, y, lab)]
                charts.show(charts.scatter(rows, f"Search interest in {keyword}, by state (index, 0 to 100)"))
    with head:
        heading(key, 4)
        if not (f.empty or plot.empty):
            ui.found(f"For {keyword}, interest and the 2020 to 2024 margin shift have a correlation of {r_val:.2f} across {len(used)} states. "
                     "Describes these states only.")
    footer(key, csv, "search_by_state.csv", ["google_trends", "medsl_president"],
           "The download keeps small states even when they are left out of the chart. The small_state column marks them.")

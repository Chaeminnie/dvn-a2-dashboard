"""The four principal views. Each render_* function draws inside the container
that the q*_page.py file opens (key = view id). Filtering happens here so the
exported CSV holds exactly the records the charts summarise."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src import charts, ui
from src.data import BASELINE_WEEKS, summarise
from src.load import jitter, records

VARIANTS = ui.VARIANTS
BLUE, TEAL, CORAL = charts.RULES, charts.PEOPLE, charts.CASES

UNIT_Q1 = "weeks from the takeover week (negative = rules tightened first)"
UNIT_Q2 = "response category per country and variant; policy strictness in index points (0 to 100)"
UNIT_Q3 = "change from the weeks -8 to -5 level (stringency index points and workplace visit percentage points)"
UNIT_Q4 = "peak cases divided by starting cases (times, log scale)"
TITLES = {
    "who_moved_first": "Who moved first?",
    "response_differs": "How did governments' response differ across variants?",
    "people_vs_rules": "Did people move before the rules?",
    "outcomes_by_timing": "How did outcomes differ by response timing?",
}


def span(colour: str, text: str) -> str:
    return f'<span style="color:{colour}">{text}</span>'


def how_to(items: list[str]) -> None:
    body = "".join(f"<li>{i}</li>" for i in items)
    st.markdown(f'<div class="how"><div class="eyebrow">How to read this chart</div><ul>{body}</ul></div>',
                unsafe_allow_html=True)


def found(text: str) -> None:
    st.markdown(f'<div class="found">{text}</div>', unsafe_allow_html=True)


def heading(key: str, number: int) -> None:
    st.markdown(f'<div class="eyebrow">Question {number}</div>', unsafe_allow_html=True)
    st.subheader(TITLES[key])


# ------------------------------------------------------------ filters ------
def seed_filters(prefix: str, frame: pd.DataFrame, strict: bool = True) -> None:
    ui.seed(f"{prefix}_continent", sorted(frame["continent"].unique()))
    ui.seed(f"{prefix}_countries", sorted(frame["country"].unique()))
    if strict:
        ui.seed(f"{prefix}_strictness", (0.0, 100.0))
    ui.seed(f"{prefix}_highlight", "None")


def filter_widgets(prefix: str, frame: pd.DataFrame, strict: bool = True, highlight: bool = True):
    """Continent, countries, strictness and highlight, inside one expander."""
    with st.expander("More filters"):
        continents = st.multiselect("Continent", sorted(frame["continent"].unique()), key=f"{prefix}_continent")
        countries = st.multiselect("Countries (select several)", sorted(frame["country"].unique()),
                                   key=f"{prefix}_countries")
        rng = None
        if strict:
            rng = st.slider("Policy strictness at takeover (0 to 100)", 0.0, 100.0, step=5.0, format="%.0f",
                            key=f"{prefix}_strictness")
        hl = None
        if highlight:
            hl = st.selectbox("Highlight one country", ui.highlight_options(frame), key=f"{prefix}_highlight")
    return continents, countries, rng, (None if hl in (None, "None") else hl)


def apply(frame: pd.DataFrame, continents, countries, rng=None) -> pd.DataFrame:
    out = frame[frame["continent"].isin(continents) & frame["country"].isin(countries)]
    if rng is not None:
        out = out[out["baseline_stringency"].between(rng[0], rng[1])]
    return out


def footer(units: str, ids: list[str], frame: pd.DataFrame, date_column: str, key: str, name: str,
           csv: pd.DataFrame) -> None:
    st.caption(f"Unit: {units}")
    ui.attribution(ids)
    ui.latest_caption(frame, date_column)
    ui.download(csv, key, name)


# --------------------------------------------------------------- Q1 --------
def _gap_text(row) -> str:
    if pd.notna(row["policy_minus_cases"]):
        gap = int(row["policy_minus_cases"])
        if gap < 0:
            return f"Rules first by {-gap} wk"
        if gap > 0:
            return f"Cases first by {gap} wk"
        return "Same week"
    return str(row["sequence"])


def render_who_moved_first(summary: pd.DataFrame, panel: pd.DataFrame) -> None:
    key = "who_moved_first"
    seed_filters("q1", summary)
    ui.seed("q1_variant", "Delta")
    ui.seed("q1_view", "Dumbbell")
    ui.seed("q1_sort", "Rules first at top")
    head = st.container()
    body = st.container()
    with body:
        view = st.radio("View", ["Dumbbell", "Heatmap pair", "World map"], horizontal=True, key="q1_view")
        c1, c2 = st.columns(2)
        variant = c1.selectbox("Variant", VARIANTS, key="q1_variant")
        sort = c2.selectbox("Sort", ["Rules first at top", "Country A to Z", "Strictness at takeover"],
                            key="q1_sort")
        continents, countries, rng, hl = filter_widgets("q1", summary)
        f = apply(summary[summary["variant"] == variant], continents, countries, rng)
        both = f[f["policy_week"].notna() & f["cases_week"].notna()]
        solo = f[f["policy_week"].isna() & f["cases_week"].notna()]
        none_row = f[f["cases_week"].isna()]
        if f.empty:
            st.info(ui.EMPTY_MESSAGE)
        else:
            gap = both["policy_minus_cases"].astype(float)
            m1, m2, m3 = st.columns(3)
            m1.metric("Rules first", int((gap < 0).sum()))
            m2.metric("Cases first", int((gap > 0).sum()))
            m3.metric("Same week", int((gap == 0).sum()))
            if hl:
                row = f[f["country"] == hl]
                st.metric(f"{hl}, {variant}", _gap_text(row.iloc[0]) if len(row) else "No event in this selection")
            if view == "Dumbbell":
                ui.legend((BLUE, "Rules got stricter"), (CORAL, "Cases started rising"))
            elif view == "Heatmap pair":
                ui.legend((BLUE, "Rules: points stricter than before"), (CORAL, "Cases: times doubled since before"))
            else:
                ui.legend((BLUE, "Rules first"), (CORAL, "Cases first"), (charts.GREY, "No gap to show"))
            order_key = {"Rules first at top": ["policy_minus_cases", "country"],
                         "Country A to Z": ["country"], "Strictness at takeover": ["baseline_stringency", "country"]}[sort]
            ascending = [False if sort == "Strictness at takeover" else True] + [True] * (len(order_key) - 1)
            ordered = both.sort_values(order_key, ascending=ascending)
            if view == "Dumbbell":
                extra = solo.sort_values("country").head(10)
                rows = records(pd.concat([ordered, extra])[["country", "policy_week", "cases_week", "baseline_stringency"]]
                               .rename(columns={"country": "c", "policy_week": "pw", "cases_week": "cw",
                                                "baseline_stringency": "bs"}))
                charts.show(charts.dumbbell(rows, [r["c"] for r in rows], hl), width="stretch")
            elif view == "Heatmap pair":
                names = list(ordered["country"])
                step = max(1, -(-len(names) // 30))
                shown = [n for i, n in enumerate(names) if i % step == 0 or n == hl]
                heat = heat_frame(panel)
                heat = heat[(heat["v"] == variant) & heat["c"].isin(shown)]
                charts.show(charts.heat_pair(records(heat), shown), width="stretch")
                if step > 1:
                    st.caption(f"Showing every {step}th of {len(names)} countries. Use the country filter to choose your own.")
            else:
                values = [{"n": charts.MAP_NAMES.get(r.country, r.country), "c": r.country, "gap": int(r.policy_minus_cases)}
                          for r in both.itertuples()]
                charts.show(charts.world_map(values, hl), width="stretch")
                st.caption("Small countries and island states are too small to draw at this scale.")
            st.caption(f"{len(solo) + len(none_row)} of {len(f)} countries have only one event or none, so they cannot show a gap.")
    with head:
        heading(key, 1)
        st.markdown(f"{span(BLUE, 'Blue')}: rules got stricter first. {span(CORAL, 'Coral')}: cases rose first. Grey: no event, or too small to draw.",
                    unsafe_allow_html=True)
        if not f.empty:
            gap = both["policy_minus_cases"].astype(float)
            found(f"{variant}: where both happened ({len(both)} countries), rules came first in {int((gap < 0).sum())}, "
                  f"cases first in {int((gap > 0).sum())}, and the same week in {int((gap == 0).sum())}. "
                  f"In {len(solo)} more, cases rose and rules never tightened.")
    footer(UNIT_Q1, ui.CORE + ["natural_earth_boundaries"], summary, "event_week", "q1_download",
           "who_moved_first.csv", f)


@st.cache_data
def heat_frame(panel: pd.DataFrame) -> pd.DataFrame:
    low, high = BASELINE_WEEKS
    rows = []
    for (_, variant), g in panel.groupby(["country_code", "variant"]):
        base = g[g["rel_week"].between(low, high)]
        bs, bc = base["stringency_index"].mean(), base["cases_per_million"].mean()
        if np.isnan(bs) or np.isnan(bc):
            continue
        w = g[g["rel_week"].between(-4, 8)]
        rows.append(pd.DataFrame({
            "c": g["country"].iloc[0], "v": variant, "w": w["rel_week"].to_numpy(),
            "rules": (w["stringency_index"] - bs).round(1).to_numpy(),
            "cases": np.log2(np.maximum(w["cases_per_million"], 1) / max(bc, 1)).round(2).to_numpy()}))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["c", "v", "w", "rules", "cases"])


# --------------------------------------------------------------- Q2 --------
def render_response_differs(summary: pd.DataFrame) -> None:
    key = "response_differs"
    seed_filters("q2", summary)
    ui.seed("q2_view", "Response matrix")
    head = st.container()
    body = st.container()
    with body:
        view = st.radio("View", ["Response matrix", "Slopegraph"], horizontal=True, key="q2_view")
        st.caption("Compares all three variants, so there is no variant filter here.")
        continents, countries, rng, hl = filter_widgets("q2", summary)
        f = apply(summary, continents, countries, rng)
        if f.empty:
            st.info(ui.EMPTY_MESSAGE)
            meds = pd.DataFrame()
        else:
            meds = f.groupby("variant")["baseline_stringency"].agg(["median", "count"]).reindex(VARIANTS)
            st.caption("Median policy strictness before takeover (0 to 100)")
            cols = st.columns(3)
            for col, v in zip(cols, VARIANTS):
                if pd.notna(meds.loc[v, "median"]):
                    col.metric(f"{v}, {int(meds.loc[v, 'count'])} countries", f"{meds.loc[v, 'median']:.0f} / 100")
                else:
                    col.metric(v, "no data")
            by = {c: g.set_index("variant") for c, g in f.groupby("country")}
            if view == "Response matrix":
                full = [c for c, g in by.items() if all(v in g.index for v in VARIANTS)]
                if not full:
                    st.caption("No country in this selection has events for all three variants. Widen the filters.")
                else:
                    rank = lambda c, v: charts.KINDS.index(by[c].loc[v, "sequence"])  # noqa: E731
                    order = sorted(full, key=lambda c: (rank(c, "Omicron"), rank(c, "Delta"), c))
                    rows = [{"c": c, "v": v, "k": charts.KIND_LABELS[rank(c, v)], "hl": c == hl}
                            for c in full for v in VARIANTS]
                    ui.legend(*[(colour, label) for colour, label in zip(charts.KIND_COLOURS, charts.KIND_LABELS)])
                    charts.show(charts.matrix(rows, order), width="content")
            else:
                rows = [{"c": c, "v": v, "bs": float(g.loc[v, "baseline_stringency"]), "hl": c == hl}
                        for c, g in by.items() if len(g) >= 2 for v in VARIANTS if v in g.index]
                medians = [{"v": v, "m": float(meds.loc[v, "median"])} for v in VARIANTS if pd.notna(meds.loc[v, "median"])]
                if rows:
                    charts.show(charts.slope(rows, medians), width="stretch")
                else:
                    st.caption("No country in this selection has events for two or more variants.")
    with head:
        heading(key, 2)
        st.markdown({
            "Response matrix": f"{span(BLUE, 'Blue')}: rules got stricter first. {span(CORAL, 'Coral')}: cases rose first. Only countries with all three variants.",
            "Slopegraph": f"Grey: one country each. Black: the median. {span(CORAL, 'Coral')}: your highlighted country.",
        }[view], unsafe_allow_html=True)
        if not f.empty and meds["median"].notna().all():
            m = meds["median"]
            found(f"Governments started each wave with {'fewer' if m.iloc[0] > m.iloc[2] else 'more'} rules in place: "
                  f"{m.iloc[0]:.0f}, then {m.iloc[1]:.0f}, then {m.iloc[2]:.0f}. This shows a change in starting point. "
                  "It does not show that governments learned.")
    footer(UNIT_Q2, ui.CORE, summary, "event_week", "q2_download", "response_differs.csv", f)


# --------------------------------------------------------------- Q3 --------
MIN_N = 5


def curve_rows(panel: pd.DataFrame) -> pd.DataFrame:
    low, high = BASELINE_WEEKS
    parts = []
    for _, g in panel.groupby(["country_code", "variant"]):
        base = g[g["rel_week"].between(low, high)]
        bs, bm = base["stringency_index"].mean(), base["workplace_mobility"].mean()
        if np.isnan(bs) or np.isnan(bm):
            continue
        parts.append(pd.DataFrame({"cc": g["country_code"].iloc[0], "w": g["rel_week"].to_numpy(),
                                   "Rules": (g["stringency_index"] - bs).to_numpy(),
                                   "People": (-(g["workplace_mobility"] - bm)).to_numpy()}))
    if not parts:
        return pd.DataFrame(columns=["s", "w", "m", "q1", "q3", "n"])
    allc = pd.concat(parts)
    out = []
    for series in ("Rules", "People"):
        a = allc.groupby("w")[series].agg(m="median", q1=lambda z: z.quantile(.25), q3=lambda z: z.quantile(.75), n="count").reset_index()
        a["s"] = series
        out.append(a[a["n"] >= MIN_N])
    return pd.concat(out, ignore_index=True)


def render_people_vs_rules(panel: pd.DataFrame) -> None:
    key = "people_vs_rules"
    ui.seed("q3_variant", "Delta")
    seed_filters("q3", panel, strict=False)
    heading_area = st.container()
    v_col, _ = st.columns([1, 3])
    variant = v_col.selectbox("Variant", VARIANTS, key="q3_variant")
    continents, countries, _, _ = filter_widgets("q3", panel, strict=False, highlight=False)
    f = panel[(panel["variant"] == variant) & panel["continent"].isin(continents) & panel["country"].isin(countries)]
    with heading_area:
        heading(key, 3)
        st.markdown(f"{span(BLUE, 'Rules')} goes up when rules get stricter. {span(TEAL, 'People')} goes up when workplace visits fall. "
                    "Lines are medians; the band is the middle half.", unsafe_allow_html=True)
        read_slot = st.empty()
    if f.empty:
        st.info(ui.EMPTY_MESSAGE)
    else:
        rows = curve_rows(f)
        events = summarise(f)
        cw = events["cases_week"].dropna()
        cases_week = float(cw.median()) if len(cw) else None
        n_countries = f["country_code"].nunique()
        m1, m2, m3 = st.columns(3)
        m1.metric("Countries in the chart", n_countries)
        m2.metric("Median week cases start rising", "none" if cases_week is None else f"{cases_week:+.0f}")
        end = rows[(rows["w"] == 8) & (rows["s"] == "Rules")]
        m3.metric("Median rules change at week +8", "no data" if end.empty else f"{end['m'].iloc[0]:+.1f} pts")
        if rows.empty:
            st.caption(f"Fewer than {MIN_N} countries have data at any week, so no medians are drawn.")
        else:
            charts.show(charts.curves(records(rows), cases_week), width="stretch")
        pe = rows[(rows["w"] == 8) & (rows["s"] == "People")]
        if not end.empty and not pe.empty:
            r, p = end["m"].iloc[0], pe["m"].iloc[0]
            read_slot.markdown(
                f'<div class="found">{variant}, median country: eight weeks after takeover, rules are {abs(r):.1f} points '
                f'{"stricter" if r >= 0 else "looser"} than before, and workplace visits are {abs(p):.1f} points '
                f'{"lower" if p >= 0 else "higher"}. Cases start rising around week {cases_week:+.0f}.</div>'
                if cases_week is not None else "", unsafe_allow_html=True)
    if variant == "Omicron":
        st.caption("Omicron took over in December and January, when people stay away from work anyway. Part of the People line is the holiday.")
    footer(UNIT_Q3, ui.CORE, panel, "date", "q3_download", "people_vs_rules.csv", f)


# --------------------------------------------------------------- Q4 --------
def render_outcomes_by_timing(summary: pd.DataFrame) -> None:
    key = "outcomes_by_timing"
    seed_filters("q4", summary)
    ui.seed("q4_variants", list(VARIANTS))
    ui.seed("q4_view", "By response type")
    ui.seed("q4_colour", "Nothing")
    head = st.container()
    body = st.container()
    with body:
        view = st.radio("View", ["By response type", "Every event"], horizontal=True, key="q4_view")
        c1, c2 = st.columns(2)
        variants = c1.multiselect("Variants", VARIANTS, key="q4_variants")
        colour = c2.selectbox("Colour dots by", ["Nothing", "Median age of country"], key="q4_colour")
        continents, countries, rng, hl = filter_widgets("q4", summary)
        f = apply(summary[summary["variant"].isin(variants)], continents, countries, rng)
        use = f[f["peak_growth"].notna() & f["sequence"].isin(charts.GROUPS)].copy()
        if f.empty:
            st.info(ui.EMPTY_MESSAGE)
        elif use.empty:
            st.caption("No events with both a growth value and a response type in this selection.")
        else:
            use["grp"] = use["sequence"].map(charts.GROUPS)
            age = use["median_age"]
            use["band"] = np.where(age.isna(), "unknown", np.where(age < 30, "younger (<30)", np.where(age < 40, "middle (30 to 40)", "older (40+)")))
            use["j"] = jitter(len(use))
            use["hl"] = use["country"] == hl
            use["gap"] = use["policy_minus_cases"]
            data = records(use.rename(columns={"country": "c", "variant": "v", "peak_growth": "g"})
                           [["c", "v", "g", "grp", "band", "j", "hl", "gap"]])
            by_age = colour != "Nothing"
            med = use.groupby("grp")["peak_growth"].median()
            cnt = use.groupby("grp")["peak_growth"].count()
            m1, m2, m3 = st.columns(3)
            m1.metric("Median: rules first", f"{med.get('Rules first', float('nan')):.0f}×" if "Rules first" in med else "no events")
            m2.metric("Median: no tightening", f"{med['Rules never tightened']:.0f}×" if "Rules never tightened" in med else "no events")
            m3.metric("Events compared", len(use))
            if by_age:
                ui.legend((charts.GREY, "Younger country (median age under 30)"), (TEAL, "Middle (30 to 40)"), ("#111111", "Older (over 40)"))
            if view == "By response type":
                charts.show(charts.box_strip(data, by_age), width="stretch")
            else:
                scatter = [d for d in data if d["gap"] is not None]
                if scatter:
                    charts.show(charts.event_scatter(scatter, by_age), width="stretch")
                else:
                    st.caption("No events have both signals in this selection.")
    with head:
        heading(key, 4)
        if not f.empty and not use.empty:
            a = med.get("Rules first")
            b = med.get("Rules never tightened")
            if a is not None and b is not None:
                found(f"Median peak was {a:.0f}× the starting level where rules came first ({int(cnt['Rules first'])} events) "
                      f"and {b:.0f}× where they never tightened ({int(cnt['Rules never tightened'])}). The groups overlap a lot.")
            else:
                found("Too few events in this selection to compare the two groups.")
    footer(UNIT_Q4, ui.CORE, summary, "event_week", "q4_download", "outcomes_by_timing.csv", f)

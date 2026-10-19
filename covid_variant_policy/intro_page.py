from __future__ import annotations

import streamlit as st

from src import charts, ui, views
from src.load import get_panel, get_summary, jitter, records

panel = get_panel()
summary = get_summary()
BLUE, CORAL = charts.RULES, charts.CASES


def frame(anchor: str, eyebrow: str):
    st.markdown(f'<div id="{anchor}" class="frame"></div>', unsafe_allow_html=True)
    left, right = st.columns([5, 7], gap="large")
    left.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    return left, right


def delta_rows(limit: int):
    d = summary[(summary["variant"] == "Delta") & summary["policy_week"].notna() & summary["cases_week"].notna()]
    d = d.sort_values(["policy_minus_cases", "country"])
    step = max(1, -(-len(d) // limit))
    d = d.iloc[::step].head(limit)
    return d


st.markdown(
    '<div class="meta">Contents: <a href="#f1">Question</a> · <a href="#f2">Takeover week</a> · '
    '<a href="#f3">Reading the charts</a> · <a href="#f4">Comparing countries</a> · <a href="#f5">Four questions</a> · '
    '<a href="#f6">Filters</a> · <a href="#f7">Data and limits</a> · <a href="#f8">Explore</a></div>',
    unsafe_allow_html=True,
)

# 1 ------------------------------------------------------------------------
l, r = frame("f1", "The research question")
with l:
    st.title("When a new variant took over, who moved first: the rules, or the cases?")
with r:
    st.write("Every country faced the same variants in the same months. In some, governments tightened the rules "
             "before cases climbed. In others, cases climbed first. In many, the rules never tightened at all.")
    st.caption("This page teaches you to read the charts. The Dashboard lets you explore them.")

# 2 ------------------------------------------------------------------------
l, r = frame("f2", "What is a takeover week?")
n_events = len(summary)
with l:
    st.markdown(f'<div class="big">{n_events}</div>', unsafe_allow_html=True)
with r:
    st.header("moments when a variant became the majority.")
    first = int((summary["sequence"] == "Containment tightened first").sum())
    never = int((summary["sequence"] == "Cases rose, containment did not tighten").sum())
    st.write(f"They span {summary['country'].nunique()} countries and three variants. In {first} of them rules "
             f"tightened before cases rose. In {never}, cases rose and the rules never tightened.")
    st.write("We call the first week a variant makes up at least half of sequenced samples its **takeover week**. "
             "That week is 0. Every other week is counted before (negative) or after (positive) it, so Delta in "
             "Mexico and Delta in Poland sit on one timeline.")
    st.caption("Source for dates: CoVariants, built on GISAID sequences. Countries that sequence little have fewer or later dates.")

# 3 ------------------------------------------------------------------------
l, r = frame("f3", "How to read the charts")
with l:
    st.header("Compare two dots.")
with r:
    views.how_to(["Each row is a country.",
                  f"The {views.span(BLUE, 'blue dot')} is the week its rules got stricter. The {views.span(CORAL, 'coral dot')} is the week its cases started rising.",
                  "The dot further left happened first. The longer the line, the longer the gap.",
                  "A single dot means the other event never happened in the window."])
    st.caption("Delta, ten countries. Weeks from takeover week.")
    d = delta_rows(10)
    rows = records(d[["country", "policy_week", "cases_week", "baseline_stringency"]]
                   .rename(columns={"country": "c", "policy_week": "pw", "cases_week": "cw", "baseline_stringency": "bs"}))
    charts.show(charts.dumbbell(rows, [x["c"] for x in rows], None, small=True), width="stretch")

# 4 ------------------------------------------------------------------------
l, r = frame("f4", "How to compare countries")
with l:
    st.header("Dark means a bigger change.")
with r:
    views.how_to(["Each row is a country, each column a week.",
                  "On the left, darker blue means rules are stricter than before.",
                  "On the right, darker coral means cases have grown more compared with before.",
                  "The two sides use different units. Compare where the colour starts, not the numbers."])
    d = delta_rows(12)
    heat = views.heat_frame(panel)
    names = list(d["country"])
    charts.show(charts.heat_pair(records(heat[(heat["v"] == "Delta") & heat["c"].isin(names)]), names, small=True, width=150),
                    width="content")

# 5 ------------------------------------------------------------------------
l, r = frame("f5", "Four questions, four ways to explore")
with l:
    st.header("The dashboard asks four things.")
with r:
    a, b = st.columns(2)
    with a:
        st.caption("**1** Who moved first?")
        d = delta_rows(7)
        rows = records(d[["country", "policy_week", "cases_week", "baseline_stringency"]]
                       .rename(columns={"country": "c", "policy_week": "pw", "cases_week": "cw", "baseline_stringency": "bs"}))
        charts.show(charts.dumbbell(rows, [x["c"] for x in rows], None, small=True), width="stretch")
    with b:
        st.caption("**2** How did governments' response differ across variants?")
        by = {c: g.set_index("variant") for c, g in summary.groupby("country")}
        rows = [{"c": c, "v": v, "bs": float(g.loc[v, "baseline_stringency"]), "hl": False}
                for c, g in by.items() if len(g) >= 2 for v in ui.VARIANTS if v in g.index]
        meds = summary.groupby("variant")["baseline_stringency"].median()
        charts.show(charts.slope(rows, [{"v": v, "m": float(meds[v])} for v in ui.VARIANTS if v in meds.index], small=True),
                        width="stretch")
    a, b = st.columns(2)
    with a:
        st.caption("**3** Did people move before the rules?")
        pf = panel[panel["variant"] == "Delta"]
        cw = views.summarise(pf)["cases_week"].dropna()
        charts.show(charts.curves(records(views.curve_rows(pf)), float(cw.median()) if len(cw) else None, small=True),
                        width="stretch")
    with b:
        st.caption("**4** How did outcomes differ by response timing?")
        use = summary[summary["peak_growth"].notna() & summary["sequence"].isin(charts.GROUPS)].copy()
        use["grp"] = use["sequence"].map(charts.GROUPS)
        use["band"] = "unknown"
        use["j"] = jitter(len(use))
        use["hl"] = False
        charts.show(charts.box_strip(records(use.rename(columns={"country": "c", "variant": "v", "peak_growth": "g"})
                                                 [["c", "v", "g", "grp", "band", "j", "hl"]]), False, small=True),
                        width="stretch")

# 6 ------------------------------------------------------------------------
l, r = frame("f6", "How to use the filters")
with l:
    st.header("Pick your countries.")
with r:
    st.markdown(
        '<div class="meta" style="border:1px solid #e4e4e7;padding:12px;display:flex;gap:24px;flex-wrap:wrap">'
        "<span>Variant<br><b style='color:#111'>Delta</b></span><span>Continent<br><b style='color:#111'>All</b></span>"
        "<span>Countries<br><b style='color:#111'>Australia, South Korea, Japan</b></span>"
        "<span>Highlight<br><b style='color:#111'>South Korea</b></span></div>", unsafe_allow_html=True)
    views.how_to(["<b>Countries</b> keeps only the countries you choose.",
                  "<b>Highlight</b> keeps everyone and makes one stand out.",
                  "<b>Variant</b> changes questions 1, 3 and 4. Question 2 always compares all three."])

# 7 ------------------------------------------------------------------------
l, r = frame("f7", "Data, definitions and limits")
with l:
    st.header("What the numbers are, and aren't.")
with r:
    views.how_to([
        "<b>Policy strictness</b> is the Oxford COVID-19 Government Response Tracker stringency index, 0 to 100. Higher means stricter rules. It does not measure how well a country did.",
        "<b>Cases</b> are reported cases per million people. Testing differs between countries and over time.",
        "<b>People</b> are Google workplace visits compared with before the variant, shown so that fewer visits points up. This data ends on 2022-08-19.",
        "<b>Rules tightened</b> means at least 5 points above the level eight to five weeks before the takeover. <b>Cases rose</b> means at least 1.5 times that level. These thresholds are our choice.",
        "Order is not cause. Countries differ in vaccination, age and many other things."])

# 8 ------------------------------------------------------------------------
l, r = frame("f8", "Explore the data")
with l:
    st.header("Start with a country you know.")
with r:
    names = sorted(summary["country"].unique())
    pick = st.selectbox("Country", names, index=names.index("South Korea") if "South Korea" in names else 0, key="start_pick")
    if st.button("Start with question 1", key="start_button"):
        for q in ("q1", "q2", "q4"):
            st.session_state[f"{q}_highlight"] = pick
        st.switch_page("q1_page.py")

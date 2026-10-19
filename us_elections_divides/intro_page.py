from __future__ import annotations

import streamlit as st

from src import charts, ui, views
from src.load import get

voters = get("voter_groups")
states = get("state_results")
monthly = get("search_monthly")
shift = get("state_search_shift")

st.title("Who divides American voters, and did online phrases move with them?")
st.markdown(
    '<p class="lede">Five elections, four ways to split voters, fifty states and a few political phrases that took off in search. '
    "The dashboard lines them up. It does not claim that one caused the other.</p>", unsafe_allow_html=True)


def frame(number: str, title: str, text: str):
    st.markdown('<div class="frame">', unsafe_allow_html=True)
    a, b = st.columns([5, 7], gap="large")
    with a:
        st.markdown(f'<div class="eyebrow">{number}</div>', unsafe_allow_html=True)
        st.header(title)
        st.markdown(text)
    return b


with frame("01 · The question", "Two things to compare",
           "First: how far apart do groups of voters sit, by gender, income and region, and how did that change between elections? "
           "Second: when did a phrase like MAGA, tradwife or manosphere take off in searches, and did anything change around then?\n\n"
           "Three words are used throughout. A **divide** is how different two groups' votes are. A **shift** is how that changes between "
           "elections. A **phrase taking off** is a search term whose interest rose.") as b:
    f24 = voters[voters["election_year"] == 2024]
    rows = views.gap_rows(f24, "None")
    st.markdown('<div class="eyebrow">Who leans which way, 2024</div>', unsafe_allow_html=True)
    charts.show(charts.dot_plot(rows, [r["r"] for r in rows], size_mode=False, domain=(25, 80)))
st.markdown("</div>", unsafe_allow_html=True)

with frame("02 · Two measures, two questions", "Size is not direction",
           "Every divide is shown two ways, never mixed. **Size** is the gap between two groups, with no side taken. **Direction** is which party each "
           "group leans to.\n\nBoth use the two-party vote: Democratic and Republican votes only, with other candidates left out. Turnout is a "
           "different thing and is shown on its own.") as b:
    st.markdown('<div class="eyebrow">An illustration, not data</div>', unsafe_allow_html=True)
    charts.show(charts.size_vs_direction())
    st.caption("Group A votes 60% Democratic and group B 40%. The size of the divide is 20 points. In direction, A leans 10 points Democratic and B 10 points Republican.")
st.markdown("</div>", unsafe_allow_html=True)

with frame("03 · Where", "Fifty states, equal tiles",
           "Each square is one state, the same size, so a small state is as visible as a large one. Colour shows how the Democratic minus Republican "
           "margin moved between two elections.") as b:
    f = states[states["election_year"] == 2024]
    items = []
    for r in f.itertuples(index=False):
        fill, ink = ui.lean_fill(r.shift_pp, 12)
        items.append({"code": r.state_code, "name": r.state, "fill": fill, "ink": ink, "v": ui.sgn(r.shift_pp),
                      "tip": f"{ui.sgn(r.shift_pp)} pp since 2020"})
    st.markdown('<div class="eyebrow">Change in margin, 2020 to 2024</div>', unsafe_allow_html=True)
    ui.ramp_legend([ui.REP, ui.MID, ui.DEM], "← Republican", "Democratic →")
    charts.show(charts.tiles(charts.prepare_tiles(items)))
st.markdown("</div>", unsafe_allow_html=True)

with frame("04 · When a phrase took off", "Search interest is not the start of an idea",
           "Google Trends shows relative interest, scaled 0 to 100. A phrase can exist for years before it is searched a lot. The amber dot marks "
           "the first month interest passes half of its peak.") as b:
    series = monthly[monthly["keyword"] == "tradwife"].sort_values("date")
    dates, vals = series["date"].tolist(), series["interest"].astype(int).tolist()
    i = views.boom_index(vals, 50, "First month")
    gaps = {}
    for e in views.ELECTIONS:
        g = voters[(voters.election_year == e) & (voters.factor == "Gender") & (voters.age_band == "18-29")]
        gaps[e] = abs(float(g[g.group == "Women"].dem_share_pct.iloc[0]) - float(g[g.group == "Men"].dem_share_pct.iloc[0]))
    boom = {"d": dates[i], "v": vals[i], "align": "right", "dx": -10, "label": f"First month at or above 50% of peak: {dates[i][:7]}"}
    gap_rows = [{"d": views.ELECTION_DAY[e], "g": gaps[e], "gl": f"{gaps[e]:.1f}", "tag": views.election_label(e), "sz": 70}
                for e in sorted(views.ELECTIONS)]
    elections = [{"d": views.ELECTION_DAY[e], "tag": views.election_label(e)} for e in sorted(views.ELECTIONS)]
    charts.show(charts.phrase_gap([{"d": d, "v": v} for d, v in zip(dates, vals)], elections, boom, gap_rows, "tradwife",
                                  "Size of the gender gap, ages 18-29 (points)", 12))
st.markdown("</div>", unsafe_allow_html=True)

with frame("05 · What this can say", "Moving together is not causing",
           "People who already lean one way may search for a phrase, so the order can run the other way. State figures cannot show what one voter did. "
           "Surveys record what people say they did.\n\nWhat the dashboard can do is show where and among whom things moved while a phrase was rising.") as b:
    x = shift[shift["keyword"] == "tradwife"].dropna(subset=["interest"])
    rows = [{"name": r.state, "x": float(r.interest), "y": float(r.shift_2020_2024), "col": ui.DEM if r.shift_2020_2024 >= 0 else ui.REP, "lab": ""}
            for r in x.itertuples(index=False)]
    st.markdown('<div class="eyebrow">Search interest in tradwife and margin shift, one dot per state</div>', unsafe_allow_html=True)
    charts.show(charts.scatter(rows, "Search interest in tradwife, by state (index, 0 to 100)"))
    if st.button("Start with question 1", key="intro_cta"):
        st.switch_page("q1_page.py")
st.markdown("</div>", unsafe_allow_html=True)

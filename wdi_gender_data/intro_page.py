from __future__ import annotations

import streamlit as st

from src import charts
from src.data import INDICATORS
from src.load import get_status, records

status = get_status()
SHORT = [n for _, n, *_ in INDICATORS]

st.title("Where does gender equality exist on paper, in practice, and in the data?")
st.markdown(
    '<p class="lede">A country can have equal laws, unequal lives, and no statistics that show either. This dashboard looks at '
    "what can be seen in six World Bank indicators, and where the evidence stops. It does not rank countries on women's rights.</p>",
    unsafe_allow_html=True)

st.markdown('<div class="frame">', unsafe_allow_html=True)
a, b = st.columns([1, 1.2], gap="large")
with a:
    st.markdown('<div class="eyebrow">01 · The question</div>', unsafe_allow_html=True)
    st.header("Three layers, three kinds of evidence")
    st.markdown(
        "**On paper** is what the law says. **In practice** is what women's lives look like, such as work, school and money. "
        "**In the data** is whether anyone measures it, by sex, and how recently.\n\n"
        "The first two get most of the attention. This dashboard is about the third.")
with b:
    st.markdown(
        '<div class="card"><b>On paper</b> · Women, Business and the Law score (0 to 100)<br>'
        '<b>In practice</b> · women and men in the labour force, girls in secondary school, women in parliament, women with an account<br>'
        '<b>In the data</b> · does a value exist, and how old is it?</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="frame">', unsafe_allow_html=True)
a, b = st.columns([1, 1.6], gap="large")
with a:
    st.markdown('<div class="eyebrow">02 · What can be seen</div>', unsafe_allow_html=True)
    st.header("A country by indicator grid")
    st.write("Each row is a country and each column an indicator. A filled square means a value exists, and the number is the year "
             "of the latest one. Grey means none. Reading across a row shows what is known about one country. Reading down a "
             "column shows how widely one indicator is measured.")
with b:
    pick = ["Australia", "Brazil", "Japan", "Kenya", "Nigeria", "Pakistan", "Somalia, Fed. Rep.", "Sweden", "Yemen, Rep.", "Zimbabwe"]
    sub = status[status["country"].isin(pick)]
    rows = records(sub.assign(c=sub["country"], i=sub["indicator"],
                              yr=sub["latest_year"].astype("Int64").astype(str).replace("<NA>", ""),
                              b=sub["years_behind"], s=sub["status"], v=sub["latest_value"])[["c", "i", "yr", "b", "s", "v"]])
    charts.show(charts.matrix(rows, sorted(pick), SHORT))
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="frame">', unsafe_allow_html=True)
a, b = st.columns([1, 1.6], gap="large")
with a:
    st.markdown('<div class="eyebrow">03 · Old numbers</div>', unsafe_allow_html=True)
    st.header("Having a value is not the same as having a current one")
    st.write("Some indicators are collected every few years. Others stop. An old value still fills a square, so the grid shows "
             "the year of the last value, not only whether one exists. The chart counts, for each indicator, the countries whose latest "
             "value is current, behind, or absent.")
with b:
    counts = status.groupby(["indicator", "status"]).size().rename("n").reset_index()
    total = status["country_code"].nunique()
    counts["share"] = counts["n"] / total * 100
    counts["i"] = counts["indicator"]
    counts["s"] = counts["status"]
    counts["o"] = counts["s"].map({"Current": 0, "Behind": 1, "No value in WDI": 2})
    charts.show(charts.status_bars(records(counts[["i", "s", "n", "share", "o"]]), SHORT, total))
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="frame">', unsafe_allow_html=True)
a, b = st.columns([1, 1.6], gap="large")
with a:
    st.markdown('<div class="eyebrow">04 · Missing is not proof</div>', unsafe_allow_html=True)
    st.header("No data does not mean discrimination")
    st.write("A gap can come from limited statistical capacity, how often surveys are run, funding, or differences in definitions. "
             "It can also mean no one asked. This dashboard reports the gap. It does not say why it exists.")
with b:
    st.markdown(
        '<div class="card"><b>A missing value can mean</b><br>The survey was not run · The question was not asked by sex · '
        "The data exists but was not shared · The definition differs · The country cannot afford to collect it</div>",
        unsafe_allow_html=True)
    st.markdown('<div class="card" style="margin-top:10px"><b>It cannot tell you</b><br>Whether women in that country fare better or worse</div>',
                unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="frame">', unsafe_allow_html=True)
st.markdown('<div class="eyebrow">05 · What this can say</div>', unsafe_allow_html=True)
st.header("Where the evidence stops")
st.write("The dashboard can show which countries and indicators are well covered, where laws and outcomes seem out of step, and "
         "where observations break off. It is a way to ask better questions, not to answer them.")
if st.button("Start with question 1", key="intro_open"):
    st.switch_page("q1_page.py")
st.markdown("</div>", unsafe_allow_html=True)
st.caption("Sources: World Bank World Development Indicators and Women, Business and the Law (WBL 1.0). Data retrieved 2026-10-16.")

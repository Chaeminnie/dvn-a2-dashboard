from __future__ import annotations

import streamlit as st

st.title("About the data")
st.write(
    "**Question:** When a new SARS-CoV-2 variant became the majority of sequenced samples in a country, "
    "did the rules tighten before, with, or after reported cases began to rise, and did people change "
    "their behaviour first?"
)
st.caption(
    "Audience: public-health students and journalists comparing pandemic responses. "
    "Coverage: the first majority takeover of Alpha, Delta and Omicron (BA.1/BA.2) in countries with enough "
    "sequencing, policy and case data, 2020 to 2022."
)
st.markdown(
    """
**Takeover week.** The first week a variant family is at least 50% of sequenced samples, and the
next two sequenced weeks average at least 50%. Weeks with fewer than 30 sequences are ignored.
Sequencing is not a random sample of infections: countries sequence different shares of cases.

**Policy strictness** is the OxCGRT stringency index (0 to 100). Higher means stricter announced rules.
It does not measure how well a country did or how closely rules were followed.
"Rules got stricter" means at least 5 points above the level eight to five weeks before the takeover.

**Cases** are reported cases per million people (7-day average), which depend on testing and reporting.
"Cases rose" means at least 1.5 times the level eight to five weeks before takeover, and at least 1 per million per day.

**People** are Google workplace visits, shown so that fewer visits points up. The mirror used here ends 2022-08-19,
so late Omicron events have missing mobility.

**What this cannot show.** Timing is not causation. Countries that tightened early may differ in vaccination, age and testing, and the groups are small, so treat gaps between them as hints. Governments respond to cases, cases respond to rules.
The thresholds are analytic choices.
"""
)

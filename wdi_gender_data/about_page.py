from __future__ import annotations

import streamlit as st

st.title("About the data")
st.write(
    "**Question:** Which countries and indicators have evidence about women's economic and political position, "
    "how recent is it, and where does it stop?"
)
st.caption(
    "Audience: students, journalists and policy readers who use World Bank data and want to know what it can and cannot show. "
    "Coverage: 217 countries and economies, six World Development Indicators, 2000 to 2025 (law score to 2023). "
    "This is not a ranking of women's rights."
)
st.markdown(
    """
**Law score.** The Women, Business and the Law index (SG.LAW.INDX), WBL 1.0 series, published through the World Bank's
WDI Database Archives (file dated 2025-10-29, covering 1970 to 2023). It scores what laws say. The archive file holds weighted
points rather than the 0 to 100 score its description states: the maximum is 4,100 points up to 2019 and 3,400, 2,600, 2,100 and 1,600
in 2020 to 2023. This dashboard divides by that maximum and multiplies by 100. The set of questions behind the index changed in 2020
and again in 2022, so scores before and after those years are not strictly comparable. It is not the newer WBL 2.0 data and the two are not mixed.

**Outcomes.** Five indicators from the WDI, in the October 2026 release: women's and men's labour force participation (ILO modelled
estimates, which are model output and exist for almost every country), girls' gross secondary enrolment (UNESCO), women's seats in
national parliaments (IPU) and women's account ownership (Global Findex survey, about every three years: 2011, 2014, 2017, 2021, 2022 and 2024).

**Gaps.** A missing value means the World Bank database holds none for that year. The export marks every missing value the same
way, so zero, not applicable and not yet published cannot be told apart, and the dashboard does not try to. Causes include survey
schedules, funding and statistical capacity. A gap is not evidence of discrimination.

**Coverage, freshness, completeness.** Coverage is the share of countries with any value for an indicator. Freshness is how many
years a country's latest value is behind the newest year found for that indicator in the database. A value counts as behind when it is
more than 4 years behind (6 for the account survey). Completeness is how many of the six indicators a country has. They are shown
separately and not combined into one score.

**Reading the charts.** Colour shows how recent a value is, not how equal anything is. An empty square is a gap in the evidence, not a finding about women in that country, and the cause is not known. The law score is about what is written, not what is enforced, and two lines moving together do not show that one caused the other. Some indicators are collected every three or four years by design, so empty years between values are normal; a break at the end of a row is the signal to look at. Gross enrolment can exceed 100%.

**Ranks.** Based only on countries with both values in the current selection. Adding or removing a country changes everyone's rank.
They compare the latest value of each country, which can come from different years.

**Countries.** 217 countries and economies with a region and income group in the WDI country metadata (aggregates are removed). Region and income group follow the
World Bank classification in that file (income groups for fiscal year 2027). Afghanistan and Pakistan are in Middle East & North Africa
(moved from South Asia on 1 July 2025).
"""
)

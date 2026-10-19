from __future__ import annotations

import streamlit as st

from src.load import get

voters = get("voter_groups")

st.title("About the data")
st.write(
    "**Question:** How far apart do groups of voters sit by gender, income and region, how did the states move between elections, "
    "and did a phrase taking off in search coincide with a change?"
)
st.caption(
    "Audience: students, journalists and curious voters. Coverage: US elections 2016 to 2024, fifty states and the District of Columbia, "
    "five search phrases (2015 to 2026)."
)
st.markdown(
    f"""
**Voters.** The Cumulative CES Common Content (version 12) combines the Cooperative Election Study surveys from 2006 to 2025. This
dashboard uses 2016, 2018, 2020, 2022 and 2024: about 305,000 respondents. Shares are weighted with the survey's own weight and counted among
respondents who named a Democratic or Republican candidate (the two-party vote). In presidential years the answer is the vote for president and in midterms the vote
for the U.S. House. Answers are reported after the election, can be wrong or missing, and small groups carry wide error. Every cell here has
at least {int(voters["n_two_party"].min()):,} respondents. Income is family income: lower is under $40,000, higher is $100,000 or more. Region follows the Census regions
(Northeast, Midwest, South, West). Turnout comes from matching respondents to voter files, so it covers only matched respondents.

**States.** Presidential results are summed from the MIT Election Data and Science Lab county file (version 2026-02-25), which compiles
official state records. Some counties carry a total row and also one row per voting mode; only the total is used, so no vote is counted twice.
State totals match the national totals (2024: about 75.0 million Democratic and 77.3 million Republican votes). Only Democratic and Republican
votes are used. The margin is Democratic minus Republican share of those two. Alaska reports by district and is summed to the state. The
MIT file does not mark certification for each state in 2024.

**Search.** Google Trends is a relative index from 0 to 100 against each phrase's own peak, rounded to whole numbers. It is not a count of searches.
Monthly series run from January 2015 to September 2026 (October 2026 was still running at export). By-state values cover 2020-11-04 to 2024-11-04 and
were exported on 2026-10-15. The District of Columbia reads 100 for every phrase because of small samples, and manosphere has no value for Montana, South
Dakota and Wyoming. Phrases are never compared with each other.

**Reading the charts.** Size is the difference in the Democratic two-party share between two groups. Direction is which side of 50% a group is on. A shift in the margin mixes changes in who voted with changes in how they voted, and small states move more. A change that coincides with a search phrase is not a change it caused: people who already lean one way may search for a phrase, the boom month depends on the threshold and rule chosen, and phrases that spike at an election (MAGA each November) peak at the vote. A state is not a voter. These are survey answers, not ballots.

**Timing.** Elections are two years apart. A phrase that rose in 2025 has no later election yet. The 2026 midterm is on 3 November 2026 and is not in the data.
"""
)

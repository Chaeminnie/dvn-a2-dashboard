# Who divides American voters, and did online phrases move with them?

A Streamlit dashboard for the 2026 USA elections subject of A2 Part C. It asks:

> How far apart do groups of voters sit by gender, income and region, how did the states move between elections, and did a
> political phrase taking off in search coincide with a change?

**Audience:** students, journalists and curious voters.
**Coverage:** five US elections (2016, 2018, 2020, 2022, 2024), 50 states and the District of Columbia, five Google Trends phrases (2015 to 2026).
It lines things up. It does not claim that one thing caused another, and it is not a forecast of the 3 November 2026 midterm.

## Python and run

Python **3.11** (`requires-python = ">=3.11,<3.12"`). Dependencies are pinned in `requirements.txt` and `pyproject.toml`.

```bash
pip install -r requirements.txt
DASHBOARD_SAMPLE_MODE=1 streamlit run app.py   # offline: reads data/sample_*.csv
streamlit run app.py                           # reads data/processed_*.csv
```

The theme is dark (`.streamlit/config.toml`). Charts are drawn with `st.vega_lite_chart`, so the colours are fixed to that theme.

## Pages and views

Six pages in a sidebar (`st.navigation`): **Start here** (`intro_page.py`, five frames), one page per question (`q1_page.py` to
`q4_page.py`, each with its own controls and a link to the next question) and **About the data** (`about_page.py`, sources and limitations):

1. **What divides voters most?** (`who_divides_voters`): dot plot, heatmap or over-time grid of the gap between two groups, per election and age band.
2. **How did states move between elections?** (`state_shift`): equal-size state tiles coloured by the change in margin (or who led).
3. **Did the gap change after a phrase took off?** (`phrase_and_gap`): monthly search interest with the boom month, above the size of the chosen gap at each election.
4. **Did states that searched more move differently?** (`search_by_state`): two tile maps or a scatter of search interest against the 2020 to 2024 margin shift.

Every view has its own filters, a "How to read this chart" note, a "Read with care" note, a `Download filtered data` CSV and an empty-result message.

## Data and pipeline

| Source | Publisher | Used for |
|---|---|---|
| Cumulative CES Common Content (V12, doi:10.7910/DVN/II2DB6) | Shiro Kuriwaki, Harvard Dataverse | weighted vote shares and turnout by group |
| County Presidential Election Returns 2000-2024 (version 2026-02-25) | MIT Election Data and Science Lab | state results 2016, 2020, 2024 |
| Google Trends: interest over time and by region (United States) | Google Trends (Google LLC) | five phrases, monthly and by state |

All three are **manual downloads** (`acquisition_method: manual`). Nothing is fetched by the code. To refresh:

1. Download the CES `.dta` from the DOI above and run `python src/ces_aggregate.py --file cumulative_2006-2025.dta`. This writes `ces_aggregates.csv`
   (225 rows, no individual respondents). Copy it to `data/raw/`.
2. Download `countypres_2000-2024.csv` from the MIT Election Lab data page to `data/raw/`.
3. Export the five phrases from Google Trends (United States, "interest over time" from 2015-01-01 and "interest by region" for 2020-11-04 to 2024-11-04)
   to `data/raw/trends/` as `time_<phrase>.csv` and `state_<phrase>.csv`.

The raw files are submitted so the pipeline can process the same copies every time. The CES (doi:10.7910/DVN/II2DB6) and the MIT county returns (doi:10.7910/DVN/VOQCHQ) are licensed CC0 1.0 on their Dataverse records, and the Google Trends exports are reused with attribution to Google Trends (https://www.google.com/trends), as the Google Trends help page requires. `src/data.py` holds the pipeline:

```bash
python -m src.data                  # build + validate data/processed_*.csv from data/raw
python -m src.data --make-sample    # cut data/sample_*.csv from the processed files
DASHBOARD_SAMPLE_MODE=1 python -m src.data   # offline: rebuild processed files from the samples
python -m src.data --validate       # validate the processed files
```

**Offline transform.** With `DASHBOARD_SAMPLE_MODE=1` the pipeline validates the four sample files and rewrites the processed files.
The samples are the full processed tables (all of them are small).

### Datasets

| Dataset | Rows | One row per |
|---|---|---|
| `voter_groups` | 225 | election, split (gender, income, region), group and age band |
| `state_results` | 153 | presidential election and state (2016, 2020, 2024) |
| `search_monthly` | 705 | phrase and month (2015-01 to 2026-09) |
| `state_search_shift` | 255 | phrase and state: interest next to the 2020 to 2024 margin shift |

### Definitions

* **Size of a divide:** the absolute difference in the weighted Democratic share of the two-party vote between two groups (Women vs Men, Lower vs Higher
  income, Northeast vs South). **Direction:** a group's Democratic share compared with 50%. Other candidates are left out. Turnout is shown on its own.
* **Income:** lower is family income under $40,000, higher is $100,000 or more. **Region:** Census regions.
* **Margin:** Democratic minus Republican share of the two-party vote. **Shift:** margin minus the margin at the previous presidential election.
* **Boom month:** the first month the search index reaches the chosen share of the phrase's own peak (rule: first month, or three months in a row).
* **Small state:** fewer than 600,000 Democratic plus Republican votes in 2024 (AK, DC, DE, HI, MT, ND, RI, SD, VT, WY).

## Caveats

* The CES is a survey. Vote choice is reported after the election, in 2018 and 2022 it is the vote for the U.S. House, and small groups carry wide error.
  Every group cell has at least 600 respondents. Turnout covers only respondents matched to a voter file.
* The MIT county file has both a TOTAL row and per-mode rows for some counties. Only the total is used, so no vote is counted twice. State totals match the national
  popular vote (2024: about 75.0 million Democratic and 77.3 million Republican votes). Certification is not marked state by state for 2024.
* Google Trends values are a relative 0 to 100 index against each phrase's own peak, rounded to whole numbers. Phrases are never compared with each other.
  The District of Columbia reads 100 for every phrase (small sample) and manosphere has no value for Montana, South Dakota and Wyoming.
* A change that coincides with a phrase is not a change it caused. A state is not a voter.

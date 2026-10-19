# Where is the gender data missing?

A Streamlit dashboard for the World Development Indicators "gender data gaps" subject of A2 Part C. It asks:

> For six gender indicators, where do laws exist on paper, where do outcomes show up in practice, and where is the
> evidence itself missing or out of date?

**Audience:** development students and journalists who want to know which countries have gender data, and which do not.
**Coverage:** 2000 to 2025, 217 economies in the full data (23,228 observations, 1,302 country-indicator status rows). The offline sample keeps 52 of them (5,815 observations).

## Python and run

Python **3.11** (`requires-python = ">=3.11,<3.12"`). Dependencies are pinned in `requirements.txt` and `pyproject.toml`.

```bash
pip install -r requirements.txt
DASHBOARD_SAMPLE_MODE=1 streamlit run app.py   # offline: reads data/sample*.csv
streamlit run app.py                           # reads data/processed*.csv
```

## Pages and views

Six pages in a sidebar (`st.navigation`): **Start here** (`intro_page.py`, five frames), one page per question (`q1_page.py` to
`q4_page.py`, each with its own controls and a link to the next question) and **About the data** (`about_page.py`, sources and limitations):

1. **What can we see?** (`what_can_we_see`): coverage, freshness and completeness matrix per country and indicator.
2. **Do laws change faster than outcomes?** (`law_vs_outcomes`): law score and one outcome over time for up to three countries.
3. **Does the law score match reality?** (`law_vs_reality`): ranks of law score versus an outcome, only for countries with both.
4. **Where does evidence break?** (`evidence_breaks`): year-by-year grid showing when each indicator was recorded.

Each view has filters, a "How to read this chart" note, an empty-result message and a `Download filtered data` CSV.

## Data and pipeline

Six World Bank WDI indicators, downloaded as bulk CSVs from the World Bank Data API (`API_<code>_DS2` files and the Women,
Business and the Law archive `DS57`). Full titles, publishers and original source organisations are in `dashboard.yml` and
shown beside each view. The indicators:

| Code | Short name |
|---|---|
| SG.LAW.INDX | Law score (WBL 1.0) |
| SL.TLF.CACT.FE.ZS | Women in the labour force (ILO modelled estimate) |
| SL.TLF.CACT.MA.ZS | Men in the labour force (ILO modelled estimate) |
| SE.SEC.ENRR.FE | Girls in secondary school (gross enrolment) |
| SG.GEN.PARL.ZS | Women in parliament |
| FX.OWN.TOTL.FE.ZS | Women with an account (Global Findex) |

```bash
python -m src.data --acquire      # live: download bulk files to data/raw/ (not required offline)
python -m src.data                # build + validate data/processed*.csv
python -m src.data --make-sample  # cut data/sample*.csv
DASHBOARD_SAMPLE_MODE=1 python -m src.data   # offline: rebuild processed files from the sample
python -m src.data --validate
```

## Caveats

* **Law index rescale.** The archive file `SG.LAW.INDX` stores points, not a 0 to 100 score. The maximum is 4100 up to
  2019, then 3400 (2020), 2600 (2021), 2100 (2022) and 1600 (2023). Each year's value is divided by that year's maximum
  and multiplied by 100. The question set changed in 2020 and 2022, so the series has breaks (dashed lines on the chart).
  WBL 1.0 is not mixed with WBL 2.0. Please verify scores against wbl.worldbank.org before relying on them.
* **Missing is not proof of discrimination.** Coverage, freshness (years behind the newest year found for that indicator)
  and completeness are shown separately and never combined into one score.
* Ranks use only countries with both values in the current selection. Gross enrolment can exceed 100%.
* ILO labour force values are modelled estimates, so almost every country has one. Account ownership comes from a survey
  roughly every three years.
* Income groups are World Bank FY27 (2025 GNI per capita). Afghanistan and Pakistan are in Middle East & North Africa
  since 1 July 2025.

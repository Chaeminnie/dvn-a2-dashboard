# Did governments react to the variant, or to the cases?

A Streamlit dashboard for the SARS-CoV-2 subject of A2 Part C. It asks, for each country where
a new variant family (Alpha, Delta, Omicron BA.1/BA.2) became the majority of sequenced samples:

> Did containment policy tighten before, with, or after reported cases began to rise, and how
> did workplace mobility, cases and deaths move around the takeover week?

**Audience:** public-health students and journalists comparing pandemic responses.
**Coverage:** first majority takeover of each variant family, 2020-12 to 2022-05, in 100+ countries
with enough sequencing, policy and case data (17 countries in the offline sample).

## Python and run

Python **3.11** (`requires-python = ">=3.11,<3.12"`). Dependencies are pinned in
`requirements.txt` and `pyproject.toml`.

```bash
pip install -r requirements.txt
DASHBOARD_SAMPLE_MODE=1 streamlit run app.py   # offline: reads data/sample*.csv
streamlit run app.py                           # reads data/processed*.csv
```

## Pages and views

Two pages, linked in a top navigation bar (`st.navigation`):

* **Intro** (`intro_page.py`): an eight-frame manual with small live charts that explains the
  takeover week, the two signals, and how to read each view.
* **Questions 1 to 4** (`q1_page.py` to `q4_page.py`): one page per question in the sidebar, each with its own controls
  and a link to the next, then **About the data** (`about_page.py`). The four views:

1. **Who moved first?** (`who_moved_first`): dumbbell, heatmap pair or world map; weeks from takeover to
   the first rules tightening and the first case rise.
2. **How did governments' response differ across variants?** (`response_differs`): response
   matrix or slopegraph for countries with all three variants.
3. **Did people move before the rules?** (`people_vs_rules`): median workplace-mobility change
   against the stringency index around takeover.
4. **How did outcomes differ by response timing?** (`outcomes_by_timing`): peak case growth
   (peak cases weeks 0 to 8 divided by baseline cases) by response type; optional colour by median age.

Every view has its own filters, a "How to read this chart" note, an empty-result message, and a
`Download filtered data` CSV of the filtered records at the bottom.

## Data and pipeline

| Source | Publisher | Used for |
|---|---|---|
| CoVariants: per-country variant distributions (perCountryData.json) | CoVariants (Hodcroft Lab, University of Bern; Nextstrain and GISAID sequence data) | variant share, takeover week |
| Oxford COVID-19 Government Response Tracker: OxCGRT compact national dataset (v1) | Blavatnik School of Government, University of Oxford | stringency index |
| COVID-19 Dataset by Our World in Data (owid-covid-data.csv) | Our World in Data | cases, deaths per million |
| COVID-19 Mobility Data Aggregator: Google country reports (mobility_report_countries.csv) | ActiveConclusion (GitHub mirror of Google COVID-19 Community Mobility Reports) | workplace mobility |

Natural Earth country boundaries (world-atlas countries-110m, public domain) draw the world map; the file is stored in `data/world_110m.json`.

The four data sources were retrieved on 2026-10-11 from the public GitHub URLs in `dashboard.yml`. They are
archived snapshots: OxCGRT stopped 2022-12-31, the OWID GitHub dataset 2024-08-19, Google
mobility 2022-10 (this mirror's last observation is 2022-08-19).

`src/data.py` holds the whole pipeline:

```bash
python -m src.data --acquire        # live: download the four files to data/raw/ (not submitted)
python -m src.data                  # live: build + validate data/processed*.csv
python -m src.data --make-sample    # cut data/sample*.csv from the full processed data
DASHBOARD_SAMPLE_MODE=1 python -m src.data   # offline: rebuild processed files from the sample
python -m src.data --validate       # validate the processed files
```

**Offline transform.** With `DASHBOARD_SAMPLE_MODE=1` the pipeline validates `data/sample.csv`,
re-derives the event summary from it, checks that it equals `data/sample_summary.csv`, and
rewrites `data/processed.csv` and `data/processed_summary.csv`.

### Definitions

* **Takeover week:** first week a variant family is >= 50% of sequenced samples, where the next
  two sequenced weeks average >= 50% and the family was < 50% at least eight weeks earlier. Weeks
  with fewer than 30 sequences are ignored. Only each family's first takeover is used, inside
  fixed event windows (see `EVENT_WINDOWS`).
* **Weekly values:** the mean of the seven daily values starting on the CoVariants Monday
  (at least four days present).
* **Containment tightened:** stringency >= baseline + 5 points, searched from week -4 to +8;
  baseline = mean of weeks -8 to -5.
* **Cases rising:** cases per million per day >= max(1.5 x baseline, 1), same search window.
* **Gap** = containment week minus cases week; negative means containment tightened first.

## Limits

* Timing is not causation: governments respond to cases and cases respond to policy.
* Sequencing is not random and is concentrated in high-income countries.
* Reported cases depend on testing and reporting practice, which changed over time and differ by
  country; some countries report weekly.
* The stringency index records announced rules, not compliance or enforcement. Where baseline
  stringency is already high, a 5-point rise is hard to register (use the baseline slider).
* Mobility comes from a third-party mirror of Google's reports and ends in August 2022.
* The 5-point and 1.5x thresholds are analytic choices, not established standards.
* Small states (for example Singapore, Malta, Bahrain) are too small to draw on the 110m world map.
* Peak case growth compares reported cases, so testing changes and the Omicron holiday period affect it.

## AI use

Built with Claude (Anthropic); see `AI_DECLARATION.md` in the submission root.

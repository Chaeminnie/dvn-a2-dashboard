"""Aggregate the Cumulative CES Common Content (doi:10.7910/DVN/II2DB6) into a small CSV.

Output: ces_aggregates.csv (no individual respondents).
Run:   python ces_aggregate.py --download          # fetches the file from Dataverse, then aggregates
       python ces_aggregate.py --file path/to/cumulative_2006-2025.dta
Needs: Python 3.9+, pandas (+ pyarrow only if you use the .feather file).
"""
import argparse, json, os, sys, urllib.request
import numpy as np, pandas as pd

DOI = "doi:10.7910/DVN/II2DB6"
YEARS = {2016: "P", 2018: "M", 2020: "P", 2022: "M", 2024: "P"}   # P = presidential, M = midterm (House vote)
COLS = ["year", "case_id", "st", "gender", "birthyr", "faminc", "weight",
        "voted_pres_party", "voted_rep_party", "vv_turnout_gvm"]
# Census regions. This script is run on its own, so it keeps its own copy of the mapping in src/data.py.
REGION = {}
for region, states in {"Northeast": "CT ME MA NH RI VT NJ NY PA", "Midwest": "IL IN MI OH WI IA KS MN MO NE ND SD",
                       "South": "DE DC FL GA MD NC SC VA WV AL KY MS TN AR LA OK TX",
                       "West": "AZ CO ID MT NV NM UT WY AK CA HI OR WA"}.items():
    for state in states.split():
        REGION[state] = region
MIN_CELL = 600   # cells with fewer two-party respondents than this are flagged low_n; the dashboard says "at least 600"
INC = {"Less than 10k": "Low", "10k - 20k": "Low", "20k - 30k": "Low", "30k - 40k": "Low",
       "40k - 50k": "Middle", "50k - 60k": "Middle", "60k - 70k": "Middle", "70k - 80k": "Middle", "80k - 100k": "Middle",
       "100k - 120k": "High", "120k - 150k": "High", "150k+": "High"}   # Low <40k, Middle 40-100k, High 100k+

# Dataverse answers 403 to the default Python User-Agent, so the download identifies as a browser.
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}

def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60)

def download(dest):
    url = f"https://dataverse.harvard.edu/api/datasets/:persistentId/versions/:latest-published/files?persistentId={DOI}"
    files = json.load(fetch(url))["data"]
    names = {f["dataFile"]["filename"]: f["dataFile"]["id"] for f in files}
    print("Files in dataset:", list(names))
    pick = next((n for n in names if n.endswith(".dta")), None) or next(n for n in names if n.endswith(".feather"))
    out = os.path.join(dest, pick)
    print("Downloading", pick, "(hundreds of MB; a few minutes)")
    with fetch(f"https://dataverse.harvard.edu/api/access/datafile/{names[pick]}?format=original") as r, open(out, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    return out

def load(path):
    if path.endswith(".feather"):
        df = pd.read_feather(path, columns=COLS)
    else:
        df = pd.read_stata(path, columns=COLS, convert_categoricals=True)
    return df

def label(s):
    """Return the column as plain strings. Fails loudly if it holds bare numeric codes."""
    if pd.api.types.is_numeric_dtype(s) and not isinstance(s.dtype, pd.CategoricalDtype):
        sys.exit(f"Column {s.name} holds numeric codes, not labels. Use the .dta file (labels are kept), not the feather file.")
    return s.astype("string")

def wshare(g, w="weight"):
    tot = g[w].sum()
    return np.nan if tot <= 0 else 100 * g.loc[g["dem"] == 1, w].sum() / tot

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file"); ap.add_argument("--download", action="store_true"); ap.add_argument("--out", default="ces_aggregates.csv")
    a = ap.parse_args()
    path = a.file or (download(".") if a.download else sys.exit("Give --file or --download"))
    df = load(path)
    df = df[df["year"].isin(list(YEARS))].copy()
    print("Respondents in 2016/18/20/22/24:", len(df))
    for c in ["st", "gender", "faminc", "voted_pres_party", "voted_rep_party", "vv_turnout_gvm"]:
        df[c] = label(df[c])
    df["year"] = df["year"].astype(int)
    df["Gender"] = df["gender"].map({"Male": "Men", "Female": "Women"})
    df["Income"] = df["faminc"].map(INC)
    df["Region"] = df["st"].map(REGION)
    age = df["year"] - pd.to_numeric(df["birthyr"], errors="coerce")
    df["age_band"] = pd.cut(age, [17, 29, 44, 64, 200], labels=["18-29", "30-44", "45-64", "65+"])
    df["vote"] = np.where(df["year"].map(YEARS) == "P", df["voted_pres_party"], df["voted_rep_party"])
    df["dem"] = (df["vote"] == "Democratic").astype(int)
    df["two_party"] = df["vote"].isin(["Democratic", "Republican"])
    # validated turnout: only respondents with a validation record (matched to the voter file)
    df["has_vv"] = df["vv_turnout_gvm"].notna()
    df["voted_vv"] = df["vv_turnout_gvm"].astype("string").str.lower().str.contains("voted", na=False).astype(int)
    rows = []
    for year, g_year in df.groupby("year"):
        for factor in ["Gender", "Income", "Region"]:
            for band in ["All ages", "18-29", "30-44", "45-64", "65+"]:
                gb = g_year if band == "All ages" else g_year[g_year["age_band"] == band]
                for grp, g in gb.groupby(factor, observed=True):
                    tp = g[g["two_party"] & g["weight"].notna()]
                    vv = g[g["has_vv"] & g["weight"].notna()]
                    dem = wshare(tp)
                    trn = np.nan if len(vv) == 0 or vv["weight"].sum() <= 0 else 100 * vv.loc[vv["voted_vv"] == 1, "weight"].sum() / vv["weight"].sum()
                    rows.append(dict(year=year, election_type=YEARS[year], factor=factor, group=grp, age_band=band,
                                     n_two_party=len(tp), dem_share_pct=round(dem, 2), n_validated=len(vv),
                                     validated_turnout_pct=round(trn, 2), low_n=int(len(tp) < MIN_CELL)))
    out = pd.DataFrame(rows)
    out.to_csv(a.out, index=False)
    print("Wrote", a.out, len(out), "rows (no individual respondents).")
    print("Sanity check, all ages, Democratic share of the two-party vote (%):")
    print(out[out.age_band == "All ages"].pivot_table(index=["factor", "group"], columns="year", values="dem_share_pct").round(1))

if __name__ == "__main__":
    main()

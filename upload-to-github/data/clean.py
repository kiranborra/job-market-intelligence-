"""
clean.py — Step 2a: turn the raw API dump into a trustworthy analysis table.

WHAT THIS FIXES (all four problems found in the raw 2,588-row pull)
------------------------------------------------------------------
1. STALE POSTINGS: `created` dates went back to 2019. Anything older than
   MAX_AGE_DAYS is dropped so "current demand" actually means current.
2. JUNK SALARIES: some rows had salary_max as low as 144 (rupees). Implausible
   values are set to NULL rather than averaged into a misleading number.
3. MESSY LOCATIONS: 804 rows just said "India" with no city. We derive a `city`
   column and label the vague ones honestly as "Not specified".
4. INCONSISTENT TITLES: "Data Analyst" / "Data analyst" / "DATA ANALYST" were
   counted as three different jobs. We normalise the title and, more usefully,
   bucket every posting into a `role_group` and a `seniority` level.

It also flags that Adzuna truncates descriptions at 500 characters, which is an
honest limitation to carry into the README.

HOW TO RUN
----------
    python clean.py

Reads the newest jobs_raw_*.csv in this folder and writes jobs_cleaned_<stamp>.csv
"""

import glob
import os
import re
from datetime import datetime

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
MAX_AGE_DAYS = 90          # drop postings older than this (set None to keep all)
MIN_PLAUSIBLE_SALARY = 100_000   # annual INR; below this the value is junk/monthly
MAX_PLAUSIBLE_SALARY = 20_000_000

HERE = os.path.dirname(os.path.abspath(__file__))


def newest_raw_file():
    files = sorted(glob.glob(os.path.join(HERE, "jobs_raw_*.csv")))
    if not files:
        raise SystemExit("No jobs_raw_*.csv found. Run collect.py first.")
    return files[-1]


# ---------------------------------------------------------------------------
# Title normalisation
# ---------------------------------------------------------------------------
def clean_title(title: str) -> str:
    """Collapse whitespace and fix ALL-CAPS / all-lowercase titles."""
    t = re.sub(r"\s+", " ", str(title)).strip()
    # Only re-case if the title is clearly mis-cased, so we don't mangle "BI" -> "Bi"
    if t.isupper() or t.islower():
        t = t.title()
    return t


ROLE_RULES = [
    ("Business Intelligence", ["business intelligence", "bi developer", "bi analyst",
                               "bi engineer", "power bi", "tableau developer", "qlik"]),
    ("Data Scientist",        ["data scientist", "data science", "machine learning engineer",
                               "ml engineer", "ai engineer"]),
    ("Data Engineer",         ["data engineer", "etl developer", "big data", "data architect",
                               "database developer", "data platform"]),
    ("Business Analyst",      ["business analyst", "business systems analyst",
                               "functional analyst", "product analyst", "process analyst"]),
    ("Data Analyst",          ["data analyst", "analytics analyst", "reporting analyst",
                               "mis analyst", "insight analyst", "analytics"]),
]


def role_group(title: str, search_role: str) -> str:
    """Bucket a free-text title into one of five comparable role families.

    Checked most-specific-first so 'Senior BI Data Analyst' lands in Business
    Intelligence rather than Data Analyst. Falls back to the search term that
    found the posting, then 'Other'.
    """
    t = str(title).lower()
    for group, keywords in ROLE_RULES:
        if any(k in t for k in keywords):
            return group
    # fall back to the query that surfaced it
    s = str(search_role).lower()
    for group, keywords in ROLE_RULES:
        if any(k in s for k in keywords):
            return group
    return "Other"


SENIORITY_RULES = [
    ("Intern / Trainee", [r"\bintern\b", r"\binternship\b", r"\btrainee\b", r"\bapprentice\b"]),
    ("Manager+",         [r"\bmanager\b", r"\bhead\b", r"\bdirector\b", r"\bvp\b", r"\bvice president\b", r"\bchief\b"]),
    ("Lead / Principal", [r"\blead\b", r"\bprincipal\b", r"\bstaff\b", r"\barchitect\b"]),
    ("Senior",           [r"\bsenior\b", r"\bsr\.?\b", r"\biii\b", r"\bii\b"]),
    ("Junior / Entry",   [r"\bjunior\b", r"\bjr\.?\b", r"\bentry\b", r"\bassociate\b",
                          r"\bfresher\b", r"\bgraduate\b", r"\bi\b$"]),
]


def seniority(title: str) -> str:
    """Extract a seniority band from the title.

    This is one of the most useful columns for a job seeker: it answers
    'how much of this market is actually open to someone entry-level?'
    """
    t = str(title).lower()
    for band, patterns in SENIORITY_RULES:
        if any(re.search(p, t) for p in patterns):
            return band
    return "Mid / Unspecified"


# ---------------------------------------------------------------------------
# Location normalisation
# ---------------------------------------------------------------------------
VAGUE_LOCATIONS = {"india", "", "nan", "none"}


def extract_city(location: str) -> str:
    """Adzuna gives 'Bangalore, Karnataka' or just 'India'. Take the city part."""
    loc = re.sub(r"\s+", " ", str(location)).strip()
    if loc.lower() in VAGUE_LOCATIONS:
        return "Not specified"
    city = loc.split(",")[0].strip()
    if city.lower() in VAGUE_LOCATIONS:
        return "Not specified"
    # Common aliases so the same city isn't split across labels
    aliases = {
        "bengaluru": "Bangalore", "gurugram": "Gurgaon",
        "new delhi": "Delhi", "navi mumbai": "Mumbai",
        "thane": "Mumbai", "secunderabad": "Hyderabad",
    }
    return aliases.get(city.lower(), city.title())


REMOTE_PAT = re.compile(r"\b(remote|work from home|wfh|hybrid)\b", re.I)


def work_mode(title: str, description: str) -> str:
    text = f"{title} {description}"
    m = REMOTE_PAT.search(text)
    if not m:
        return "Not specified"
    word = m.group(1).lower()
    return "Hybrid" if word == "hybrid" else "Remote"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    src = newest_raw_file()
    print(f"Reading {os.path.basename(src)}")
    df = pd.read_csv(src)
    start_rows = len(df)
    report = []

    # --- basic integrity -----------------------------------------------------
    df = df.dropna(subset=["id", "title"])
    df = df.drop_duplicates(subset="id").reset_index(drop=True)
    report.append(("dropped blank/duplicate rows", start_rows - len(df)))

    # --- dates + staleness ---------------------------------------------------
    df["created_dt"] = pd.to_datetime(df["created"], errors="coerce", utc=True)
    now = pd.Timestamp.now(tz="UTC")
    df["days_old"] = (now - df["created_dt"]).dt.days

    if MAX_AGE_DAYS is not None:
        before = len(df)
        df = df[df["days_old"].notna() & (df["days_old"] <= MAX_AGE_DAYS)].copy()
        report.append((f"dropped postings older than {MAX_AGE_DAYS} days", before - len(df)))

    df["posted_date"] = df["created_dt"].dt.date.astype(str)
    df["posted_month"] = df["created_dt"].dt.to_period("M").astype(str)
    df["posted_week"] = df["created_dt"].dt.to_period("W").apply(lambda p: str(p.start_time.date()))

    # --- titles / roles / seniority -----------------------------------------
    df["title_clean"] = df["title"].map(clean_title)
    df["role_group"] = [role_group(t, s) for t, s in zip(df["title_clean"], df["search_role"])]
    df["seniority"] = df["title_clean"].map(seniority)

    # --- location ------------------------------------------------------------
    df["city"] = df["location"].map(extract_city)
    df["work_mode"] = [work_mode(t, d) for t, d in zip(df["title_clean"], df["description"].fillna(""))]

    # --- salary cleaning -----------------------------------------------------
    for col in ("salary_min", "salary_max"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        bad = df[col].notna() & (
            (df[col] < MIN_PLAUSIBLE_SALARY) | (df[col] > MAX_PLAUSIBLE_SALARY)
        )
        report.append((f"nulled implausible {col}", int(bad.sum())))
        df.loc[bad, col] = np.nan

    # if only one bound survived, don't invent the other
    df["salary_avg"] = df[["salary_min", "salary_max"]].mean(axis=1, skipna=True)
    df["salary_reported"] = df["salary_avg"].notna().astype(int)
    df["salary_lpa"] = (df["salary_avg"] / 100_000).round(2)   # lakh per annum, readable

    # --- description ---------------------------------------------------------
    df["description"] = df["description"].fillna("").map(lambda s: re.sub(r"\s+", " ", str(s)).strip())
    df["description_truncated"] = df["description"].str.endswith(("…", "...")).astype(int)
    df["description_len"] = df["description"].str.len()

    # --- contract type -------------------------------------------------------
    df["contract_type"] = df["contract_type"].fillna("Not specified").str.title()

    # --- final column order --------------------------------------------------
    cols = [
        "id", "title_clean", "title", "company", "city", "location", "work_mode",
        "role_group", "seniority", "category", "contract_type",
        "salary_min", "salary_max", "salary_avg", "salary_lpa", "salary_reported",
        "posted_date", "posted_week", "posted_month", "days_old",
        "description", "description_len", "description_truncated",
        "search_role", "pull_date", "redirect_url",
    ]
    df = df[[c for c in cols if c in df.columns]]

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(HERE, f"jobs_cleaned_{stamp}.csv")
    df.to_csv(out, index=False)

    # ---------------------------------------------------------------------
    # Data quality report — this is what you paste back to review
    # ---------------------------------------------------------------------
    print("\n--- CLEANING ACTIONS ---")
    for label, n in report:
        print(f"  {label}: {n}")

    print(f"\n--- RESULT: {len(df)} clean postings (from {start_rows} raw) ---")
    print(f"  saved to {os.path.basename(out)}")
    print(f"  salary usable: {df['salary_reported'].sum()} ({df['salary_reported'].mean():.0%})")
    print(f"  descriptions truncated by API: {df['description_truncated'].sum()} ({df['description_truncated'].mean():.0%})")
    print(f"  date range: {df['posted_date'].min()} to {df['posted_date'].max()}")

    print("\n--- ROLE GROUP ---")
    print(df["role_group"].value_counts().to_string())
    print("\n--- SENIORITY ---")
    print(df["seniority"].value_counts().to_string())
    print("\n--- TOP 10 CITIES ---")
    print(df["city"].value_counts().head(10).to_string())
    print("\n--- WORK MODE ---")
    print(df["work_mode"].value_counts().to_string())


if __name__ == "__main__":
    main()

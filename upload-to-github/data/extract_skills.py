"""
extract_skills.py — Step 2b: find which skills each posting asks for.

WHY THIS IS THE MOST IMPORTANT FIX IN THE PROJECT
-------------------------------------------------
The original version matched skill keywords against the job TITLE only, so just
13 of 49 postings (27%) ended up with any skill attached — which meant the
"most in-demand skills" chart was built on almost no data.

This version matches against the job DESCRIPTION using the curated taxonomy in
skill_taxonomy.py, with:
  * word boundaries, so "excel" doesn't match "excellent" and "R" doesn't match "HR"
  * alias handling, so "powerbi", "power-bi" and "DAX" all count as Power BI
  * one row per (job, skill) pair -> a proper many-to-many table for SQL joins

HONEST LIMITATION: Adzuna truncates descriptions to ~500 characters, so this
measures the skills employers mention FIRST, not every skill in the full JD.
Say that out loud in interviews; it shows you understand your own data.

HOW TO RUN
----------
    python extract_skills.py

Reads the newest jobs_cleaned_*.csv and writes job_skills_<stamp>.csv
"""

import glob
import os
import re
from datetime import datetime

import pandas as pd

from skill_taxonomy import SKILLS, RAW_REGEX_MARKERS

HERE = os.path.dirname(os.path.abspath(__file__))


def newest_cleaned_file():
    files = sorted(glob.glob(os.path.join(HERE, "jobs_cleaned_*.csv")))
    if not files:
        raise SystemExit("No jobs_cleaned_*.csv found. Run clean.py first.")
    return files[-1]


def build_patterns():
    """Compile one regex per skill from its aliases.

    Aliases that already contain regex syntax (like the careful pattern for "R")
    are used as-is; plain words get wrapped in \\b...\\b word boundaries.
    """
    compiled = {}
    for skill, (category, aliases) in SKILLS.items():
        parts = []
        for a in aliases:
            if any(m in a for m in RAW_REGEX_MARKERS):
                parts.append(a)                 # already a regex
            else:
                parts.append(rf"\b{re.escape(a)}\b")
        compiled[skill] = (category, re.compile("|".join(parts), re.IGNORECASE))
    return compiled


def main():
    src = newest_cleaned_file()
    print(f"Reading {os.path.basename(src)}")
    df = pd.read_csv(src)

    patterns = build_patterns()
    print(f"Matching {len(patterns)} skills against job descriptions...\n")

    # Search title + description together: the title is short but high-signal.
    haystack = (df["title_clean"].fillna("") + " " + df["description"].fillna("")).tolist()
    ids = df["id"].tolist()

    rows = []
    for job_id, text in zip(ids, haystack):
        for skill, (category, pat) in patterns.items():
            if pat.search(text):
                rows.append({"job_id": job_id, "skill_name": skill, "skill_category": category})

    js = pd.DataFrame(rows)
    if js.empty:
        raise SystemExit("No skills matched — check skill_taxonomy.py")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(HERE, f"job_skills_{stamp}.csv")
    js.to_csv(out, index=False)

    # ---------------------------------------------------------------------
    # Coverage report — the headline improvement over the old version
    # ---------------------------------------------------------------------
    total_jobs = len(df)
    tagged = js["job_id"].nunique()
    print(f"--- COVERAGE ---")
    print(f"  jobs with at least one skill: {tagged} of {total_jobs} ({tagged/total_jobs:.0%})")
    print(f"  (old version managed 13 of 49 = 27%)")
    print(f"  total job-skill pairs: {len(js)}")
    print(f"  avg skills per tagged job: {len(js)/tagged:.1f}")
    print(f"  saved to {os.path.basename(out)}")

    print("\n--- TOP 20 SKILLS OVERALL (% of all postings) ---")
    counts = js["skill_name"].value_counts()
    for skill, n in counts.head(20).items():
        print(f"  {skill:<26} {n:>5}  {n/total_jobs:>5.0%}")

    print("\n--- BY CATEGORY ---")
    print(js["skill_category"].value_counts().to_string())

    # Most useful cut for a job seeker: what do ENTRY-LEVEL postings ask for?
    entry = df[df["seniority"].isin(["Junior / Entry", "Intern / Trainee"])]["id"]
    if len(entry):
        je = js[js["job_id"].isin(set(entry))]
        print(f"\n--- TOP 10 SKILLS IN ENTRY-LEVEL POSTINGS ({len(entry)} jobs) ---")
        for skill, n in je["skill_name"].value_counts().head(10).items():
            print(f"  {skill:<26} {n:>5}  {n/len(entry):>5.0%}")

    print("\n--- SKILLS THAT MATCHED NOTHING (candidates to remove/fix) ---")
    missing = [s for s in SKILLS if s not in counts.index]
    print("  " + (", ".join(missing) if missing else "none — every skill matched at least once"))


if __name__ == "__main__":
    main()

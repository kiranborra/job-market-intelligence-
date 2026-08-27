"""
show_files.py — utility: where is everything the pipeline produced?

Run this any time you're not sure which file to open, or whether a step ran.
It prints the FULL path of every pipeline output, its size, its row count, and
clearly marks the two files that Power BI should load.

HOW TO RUN
----------
    python show_files.py
"""

import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def rows(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return max(sum(1 for _ in f) - 1, 0)
    except Exception:
        return "?"


def show(label, pattern, note=""):
    files = sorted(glob.glob(os.path.join(HERE, pattern)))
    print(f"\n{label}")
    if not files:
        print("   MISSING — this step has not been run yet")
        return
    for p in files:
        newest = " <-- NEWEST (the one the next step uses)" if p == files[-1] else ""
        kb = os.path.getsize(p) / 1024
        print(f"   {p}")
        print(f"      {rows(p)} rows, {kb:,.0f} KB{newest}")
    if note:
        print(f"   {note}")


print("=" * 78)
print("PIPELINE OUTPUTS")
print(f"project folder: {HERE}")
print("=" * 78)

show("STEP 1  collect.py  ->  raw API pull", "jobs_raw_*.csv")
show("STEP 2a clean.py  ->  cleaned postings", "jobs_cleaned_*.csv")
show("STEP 2b extract_skills.py  ->  job/skill pairs", "job_skills_*.csv")

db = os.path.join(HERE, "job_market.db")
print("\nSTEP 3a load_db.py  ->  SQLite database")
if os.path.exists(db):
    print(f"   {db}")
    print(f"      {os.path.getsize(db)/1024:,.0f} KB  (open with DB Browser for SQLite)")
else:
    print("   MISSING — run load_db.py")

show("STEP 3b analyze.py  ->  findings report", "analysis_output.txt")

print("\n" + "=" * 78)
print("LOAD THESE TWO INTO POWER BI  (Get Data -> Text/CSV, NOT Excel workbook)")
print("=" * 78)
exports = os.path.join(HERE, "exports")
for name, desc in [("pbi_jobs.csv", "one row per posting - the main table"),
                   ("pbi_job_skills.csv", "one row per job/skill pair - the bridge")]:
    p = os.path.join(exports, name)
    if os.path.exists(p):
        print(f"\n   {p}")
        print(f"      {rows(p)} rows - {desc}")
    else:
        print(f"\n   MISSING: {p}")
        print("      run load_db.py to create it")

print("\nThen: Model view -> drag pbi_jobs[id] onto pbi_job_skills[job_id] (one-to-many)")
print("=" * 78)

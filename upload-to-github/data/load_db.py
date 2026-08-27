"""
load_db.py — Step 3a: load the cleaned data into a normalised SQLite database.

WHY A DATABASE AND NOT JUST CSVs
--------------------------------
The analysis needs a many-to-many relationship (one job asks for many skills;
one skill appears in many jobs). Modelling that properly as three tables
(jobs / skills / job_skills) is the difference between "I made charts in Excel"
and "I designed a schema" — and it lets the interesting questions be answered
in SQL instead of by hand.

WHAT IT DOES
------------
1. Backs up any existing job_market.db (never silently destroys your old work).
2. Creates jobs, skills, job_skills with explicit primary and foreign keys.
3. Creates reusable VIEWS for each dashboard question, so the SQL lives in the
   database rather than being buried in Power BI.
4. Exports two analysis-ready CSVs into exports/ for Power BI to consume,
   because Power BI Desktop has no native SQLite connector (avoiding an ODBC
   driver install is worth it).

HOW TO RUN
----------
    python load_db.py
"""

import glob
import os
import shutil
import sqlite3
from datetime import datetime

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "job_market.db")
EXPORT_DIR = os.path.join(HERE, "exports")


def newest(pattern):
    files = sorted(glob.glob(os.path.join(HERE, pattern)))
    if not files:
        raise SystemExit(f"No {pattern} found — run the earlier steps first.")
    return files[-1]


SCHEMA = """
DROP VIEW  IF EXISTS v_skill_demand;
DROP VIEW  IF EXISTS v_skill_by_role;
DROP VIEW  IF EXISTS v_seniority_mix;
DROP VIEW  IF EXISTS v_city_demand;
DROP VIEW  IF EXISTS v_top_companies;
DROP VIEW  IF EXISTS v_weekly_postings;
DROP VIEW  IF EXISTS v_entry_level_skills;
DROP TABLE IF EXISTS job_skills;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS jobs;

CREATE TABLE jobs (
    id                    TEXT PRIMARY KEY,
    title                 TEXT NOT NULL,
    company               TEXT,
    city                  TEXT,
    location              TEXT,
    work_mode             TEXT,
    role_group            TEXT,
    seniority             TEXT,
    category              TEXT,
    contract_type         TEXT,
    salary_min            REAL,
    salary_max            REAL,
    salary_avg            REAL,
    salary_lpa            REAL,
    salary_reported       INTEGER NOT NULL DEFAULT 0,
    posted_date           TEXT,
    posted_week           TEXT,
    posted_month          TEXT,
    days_old              INTEGER,
    description           TEXT,
    description_truncated INTEGER,
    search_role           TEXT,
    pull_date             TEXT,
    redirect_url          TEXT
);

CREATE TABLE skills (
    skill_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name     TEXT NOT NULL UNIQUE,
    skill_category TEXT NOT NULL
);

CREATE TABLE job_skills (
    job_id   TEXT    NOT NULL REFERENCES jobs(id),
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id),
    PRIMARY KEY (job_id, skill_id)
);

CREATE INDEX idx_jobs_role      ON jobs(role_group);
CREATE INDEX idx_jobs_seniority ON jobs(seniority);
CREATE INDEX idx_jobs_city      ON jobs(city);
CREATE INDEX idx_js_skill       ON job_skills(skill_id);

-- ---------------------------------------------------------------------
-- VIEWS: one per dashboard question
-- ---------------------------------------------------------------------

-- Overall skill demand. NOTE: denominator is ALL postings, and because the API
-- truncates descriptions to ~500 chars these percentages UNDERSTATE real demand.
-- Label them "mentioned in posting summary", never "required".
CREATE VIEW v_skill_demand AS
SELECT s.skill_name,
       s.skill_category,
       COUNT(DISTINCT js.job_id) AS job_count,
       ROUND(100.0 * COUNT(DISTINCT js.job_id) / (SELECT COUNT(*) FROM jobs), 1) AS pct_of_postings
FROM skills s
JOIN job_skills js ON js.skill_id = s.skill_id
GROUP BY s.skill_name, s.skill_category;

-- Skill mix within each role family. This is the robust comparison: truncation
-- affects every role equally, so the RELATIVE differences are trustworthy.
CREATE VIEW v_skill_by_role AS
SELECT j.role_group,
       s.skill_name,
       s.skill_category,
       COUNT(DISTINCT j.id) AS job_count,
       ROUND(100.0 * COUNT(DISTINCT j.id) /
             (SELECT COUNT(*) FROM jobs j2 WHERE j2.role_group = j.role_group), 1) AS pct_of_role
FROM jobs j
JOIN job_skills js ON js.job_id = j.id
JOIN skills s      ON s.skill_id = js.skill_id
GROUP BY j.role_group, s.skill_name, s.skill_category;

CREATE VIEW v_seniority_mix AS
SELECT seniority,
       COUNT(*) AS job_count,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM jobs), 1) AS pct_of_postings
FROM jobs
GROUP BY seniority;

CREATE VIEW v_city_demand AS
SELECT city,
       COUNT(*) AS job_count,
       ROUND(100.0 * COUNT(*) /
             (SELECT COUNT(*) FROM jobs WHERE city <> 'Not specified'), 1) AS pct_of_located
FROM jobs
WHERE city <> 'Not specified'
GROUP BY city;

CREATE VIEW v_top_companies AS
SELECT company,
       COUNT(*) AS job_count,
       COUNT(DISTINCT city) AS cities,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM jobs), 1) AS pct_of_postings
FROM jobs
WHERE company IS NOT NULL
GROUP BY company;

CREATE VIEW v_weekly_postings AS
SELECT posted_week, role_group, COUNT(*) AS job_count
FROM jobs
GROUP BY posted_week, role_group;

-- What the small number of genuinely entry-level postings actually ask for.
CREATE VIEW v_entry_level_skills AS
SELECT s.skill_name,
       COUNT(DISTINCT j.id) AS job_count,
       ROUND(100.0 * COUNT(DISTINCT j.id) /
             (SELECT COUNT(*) FROM jobs WHERE seniority IN ('Junior / Entry','Intern / Trainee')), 1) AS pct_of_entry
FROM jobs j
JOIN job_skills js ON js.job_id = j.id
JOIN skills s      ON s.skill_id = js.skill_id
WHERE j.seniority IN ('Junior / Entry','Intern / Trainee')
GROUP BY s.skill_name;
"""

JOB_COLS = [
    "id", "title_clean", "company", "city", "location", "work_mode", "role_group",
    "seniority", "category", "contract_type", "salary_min", "salary_max", "salary_avg",
    "salary_lpa", "salary_reported", "posted_date", "posted_week", "posted_month",
    "days_old", "description", "description_truncated", "search_role", "pull_date",
    "redirect_url",
]


def main():
    jobs_csv = newest("jobs_cleaned_*.csv")
    skills_csv = newest("job_skills_*.csv")
    print(f"jobs   <- {os.path.basename(jobs_csv)}")
    print(f"skills <- {os.path.basename(skills_csv)}")

    jobs = pd.read_csv(jobs_csv)
    js = pd.read_csv(skills_csv)

    # sanity: the cleaned file must be the new format, not an old broken one
    missing = [c for c in ("id", "title_clean", "role_group", "seniority") if c not in jobs.columns]
    if missing:
        raise SystemExit(f"{os.path.basename(jobs_csv)} is missing {missing} — rerun clean.py")

    # --- back up any existing database ---------------------------------------
    if os.path.exists(DB_PATH):
        backup = os.path.join(HERE, f"job_market_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
        shutil.copy2(DB_PATH, backup)
        print(f"backed up existing database -> {os.path.basename(backup)}")

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)

    # --- jobs ----------------------------------------------------------------
    jdf = jobs[[c for c in JOB_COLS if c in jobs.columns]].copy()
    jdf = jdf.rename(columns={"title_clean": "title"})
    jdf = jdf.astype(object).where(jdf.notna(), None)
    cols = list(jdf.columns)
    con.executemany(
        f"INSERT OR REPLACE INTO jobs ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
        jdf.itertuples(index=False, name=None),
    )

    # --- skills (dimension) --------------------------------------------------
    dim = (js[["skill_name", "skill_category"]].drop_duplicates()
             .sort_values("skill_name").reset_index(drop=True))
    con.executemany("INSERT INTO skills (skill_name, skill_category) VALUES (?,?)",
                    dim.itertuples(index=False, name=None))
    id_map = dict(con.execute("SELECT skill_name, skill_id FROM skills").fetchall())

    # --- job_skills (bridge) -------------------------------------------------
    valid_jobs = set(jdf["id"])
    pairs = {(r.job_id, id_map[r.skill_name])
             for r in js.itertuples() if r.job_id in valid_jobs}
    con.executemany("INSERT OR IGNORE INTO job_skills (job_id, skill_id) VALUES (?,?)", pairs)
    con.commit()

    # --- verify --------------------------------------------------------------
    print("\n--- LOADED ---")
    for t in ("jobs", "skills", "job_skills"):
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<12}{n:>6} rows")
    orphans = con.execute(
        "SELECT COUNT(*) FROM job_skills js LEFT JOIN jobs j ON j.id=js.job_id WHERE j.id IS NULL"
    ).fetchone()[0]
    print(f"  orphaned job_skills rows: {orphans} (must be 0)")

    views = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")]
    print(f"  views created: {len(views)} -> {', '.join(views)}")

    # --- export for Power BI -------------------------------------------------
    os.makedirs(EXPORT_DIR, exist_ok=True)
    pbi_jobs = pd.read_sql_query("SELECT * FROM jobs", con).drop(columns=["description"])
    pbi_skills = pd.read_sql_query("""
        SELECT js.job_id, s.skill_name, s.skill_category
        FROM job_skills js JOIN skills s ON s.skill_id = js.skill_id
    """, con)
    pbi_jobs.to_csv(os.path.join(EXPORT_DIR, "pbi_jobs.csv"), index=False)
    pbi_skills.to_csv(os.path.join(EXPORT_DIR, "pbi_job_skills.csv"), index=False)
    print(f"\n  exports/pbi_jobs.csv       {len(pbi_jobs)} rows  <- Power BI table 1")
    print(f"  exports/pbi_job_skills.csv {len(pbi_skills)} rows  <- Power BI table 2")
    print("  (relate them one-to-many on id -> job_id)")

    con.close()
    print(f"\nDatabase ready: {os.path.basename(DB_PATH)}")


if __name__ == "__main__":
    main()

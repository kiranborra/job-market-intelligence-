"""
load_to_sql.py
---------------
Day 3 script: loads the cleaned job CSV into SQLite with 3 tables:
jobs, skills, and job_skills (a join table linking them).

Run this with: python scripts/load_to_sql.py
"""

import os
import glob
import sqlite3
import pandas as pd

DB_PATH = "data/job_market.db"


def get_latest_cleaned_csv():
    files = glob.glob("data/jobs_cleaned_*.csv")
    if not files:
        raise SystemExit("No cleaned CSV found. Run clean_data.py first.")
    latest = max(files, key=os.path.getctime)
    print(f"Using cleaned file: {latest}")
    return latest


def create_schema(conn):
    conn.executescript("""
    DROP TABLE IF EXISTS job_skills;
    DROP TABLE IF EXISTS skills;
    DROP TABLE IF EXISTS jobs;

    CREATE TABLE jobs (
        id TEXT PRIMARY KEY,
        title TEXT,
        company TEXT,
        location TEXT,
        category TEXT,
        salary_min REAL,
        salary_max REAL,
        salary_avg REAL,
        salary_reported INTEGER,
        contract_type TEXT,
        created TEXT,
        redirect_url TEXT
    );

    CREATE TABLE skills (
        skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_name TEXT UNIQUE
    );

    CREATE TABLE job_skills (
        job_id TEXT,
        skill_id INTEGER,
        FOREIGN KEY (job_id) REFERENCES jobs(id),
        FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
    );
    """)
    conn.commit()


def load_data(conn, df):
    jobs_cols = [
        "id", "title", "company", "location", "category",
        "salary_min", "salary_max", "salary_avg", "salary_reported",
        "contract_type", "created", "redirect_url",
    ]
    jobs_df = df[[c for c in jobs_cols if c in df.columns]].copy()
    jobs_df.to_sql("jobs", conn, if_exists="append", index=False)
    print(f"Loaded {len(jobs_df)} rows into jobs table.")

    cur = conn.cursor()
    link_count = 0

    for _, row in df.iterrows():
        skills_str = row.get("skills_found", "")
        if not isinstance(skills_str, str) or not skills_str.strip():
            continue

        for skill in [s.strip() for s in skills_str.split(",") if s.strip()]:
            cur.execute(
                "INSERT OR IGNORE INTO skills (skill_name) VALUES (?)", (skill,)
            )
            cur.execute(
                "SELECT skill_id FROM skills WHERE skill_name = ?", (skill,)
            )
            skill_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO job_skills (job_id, skill_id) VALUES (?, ?)",
                (row["id"], skill_id),
            )
            link_count += 1

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM skills")
    skill_count = cur.fetchone()[0]
    print(f"Loaded {skill_count} unique skills, {link_count} job-skill links.")


if __name__ == "__main__":
    csv_path = get_latest_cleaned_csv()
    df = pd.read_csv(csv_path)

    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    create_schema(conn)
    load_data(conn, df)

    conn.close()
    print(f"Done. Database ready at {DB_PATH}")
"""
clean_data.py
-------------
Day 2 script: reads the most recent raw CSV, cleans it, and extracts
a simple skills list from each job description.

Run this with: python scripts/clean_data.py
"""

import os
import re
import glob
import pandas as pd

# Edit this list to match skills relevant to the roles you're researching
# Note: avoid single-letter skills like "r" alone — too many false matches
SKILL_KEYWORDS = [
    "python", "sql", "excel", "power bi", "tableau", "r programming",
    "java", "aws", "azure", "gcp", "spark", "hadoop", "machine learning",
    "deep learning", "pandas", "numpy", "git", "docker", "kubernetes",
    "snowflake", "databricks", "etl", "nlp", "statistics",
]


def get_latest_raw_csv():
    files = glob.glob("data/jobs_raw_*.csv")
    if not files:
        raise SystemExit("No raw CSV found. Run fetch_jobs.py first.")
    latest = max(files, key=os.path.getctime)
    print(f"Using raw file: {latest}")
    return latest


def extract_skills(description):
    if not isinstance(description, str):
        return ""
    text = description.lower()
    found = [
        skill for skill in SKILL_KEYWORDS
        if re.search(r'\b' + re.escape(skill) + r'\b', text)
    ]
    return ", ".join(found)


def clean_data(df):
    before = len(df)

    df = df.drop_duplicates(subset=["id"])
    df = df.dropna(subset=["title"])
    df = df[df["company"].notna() & (df["company"].astype(str).str.strip() != "")]

    for col in ["title", "company", "location", "description"]:
        df[col] = df[col].astype(str).apply(
            lambda x: x.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
            if x != "nan" else x
        )

    df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")
    df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")
    df["salary_reported"] = df["salary_min"].notna() & df["salary_max"].notna()
    df["salary_avg"] = (df["salary_min"] + df["salary_max"]) / 2

    df["skills_found"] = df["description"].apply(extract_skills)

    for col in ["title", "company", "location"]:
        df[col] = df[col].astype(str).str.strip()

    after = len(df)
    print(f"Cleaned data: {before} rows -> {after} rows "
          f"({before - after} removed as duplicates/incomplete)")

    return df


def save_cleaned_csv(df):
    os.makedirs("data", exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"data/jobs_cleaned_{timestamp}.csv"
    df.to_csv(filepath, index=False)
    print(f"Saved cleaned data to {filepath}")
    return filepath


if __name__ == "__main__":
    raw_path = get_latest_raw_csv()
    df = pd.read_csv(raw_path)
    cleaned_df = clean_data(df)
    save_cleaned_csv(cleaned_df)
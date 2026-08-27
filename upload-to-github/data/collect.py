"""
collect.py — Step 1 of the Job Market Intelligence pipeline.

Pulls live job postings from the Adzuna API across several roles and pages,
de-duplicates them, and saves a timestamped raw CSV.

WHY THIS SCRIPT EXISTS
----------------------
The old dataset had only 49 rows from a single query on a single day, and only
~16% had salary and ~27% had any skill tagged. That's too thin to call
"intelligence". This script fixes the root cause by pulling MANY roles across
MANY pages, and — importantly — it keeps the full `description` text so the
skill-extraction step later can actually find skills (the old version matched
only against the short job title, which is why coverage was so low).

HOW TO RUN
----------
1. pip install -r requirements.txt
2. Copy .env.example to .env and paste in your Adzuna app_id and app_key.
3. python collect.py

Output: jobs_raw_YYYYMMDD_HHMMSS.csv in this folder, plus a printed row count.
"""

import os
import time
from datetime import datetime

import requests
import pandas as pd
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# CONFIG — tweak these to change how much data you pull
# ---------------------------------------------------------------------------
COUNTRY = "in"                 # Adzuna country code: "in" India, "gb" UK, "us" USA, etc.
RESULTS_PER_PAGE = 50          # Adzuna maximum is 50
PAGES_PER_ROLE = 10            # 10 pages x 50 = up to 500 postings per role
SLEEP_SECONDS = 1.2            # pause between calls so we don't hit the rate limit
MAX_DAYS_OLD = None            # e.g. 30 to only keep recent postings; None = no limit

# The roles we search for. Add or remove to change the scope of the dataset.
ROLES = [
    "data analyst",
    "business analyst",
    "data engineer",
    "data scientist",
    "business intelligence analyst",
    "bi developer",
]

BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"


def get_credentials():
    """Load Adzuna API keys from the .env file and fail loudly if they're missing."""
    load_dotenv()
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        raise SystemExit(
            "\nERROR: Adzuna credentials not found.\n"
            "  1. Copy .env.example to a file named .env\n"
            "  2. Put your ADZUNA_APP_ID and ADZUNA_APP_KEY inside it\n"
            "  3. Run this script again.\n"
            "Get free keys at https://developer.adzuna.com/\n"
        )
    return app_id, app_key


def fetch_page(app_id, app_key, role, page):
    """Fetch a single page of results for one role. Returns a list of raw job dicts."""
    url = BASE_URL.format(country=COUNTRY, page=page)
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": RESULTS_PER_PAGE,
        "what": role,
        "content-type": "application/json",
    }
    if MAX_DAYS_OLD:
        params["max_days_old"] = MAX_DAYS_OLD

    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        print(f"    ! {role} p{page}: HTTP {resp.status_code} — stopping this role")
        return None
    return resp.json().get("results", [])


def parse_job(job, role):
    """Pull just the fields we care about out of Adzuna's nested JSON."""
    return {
        "id": job.get("id"),
        "title": job.get("title"),
        "company": (job.get("company") or {}).get("display_name"),
        "location": (job.get("location") or {}).get("display_name"),
        "category": (job.get("category") or {}).get("label"),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "description": job.get("description"),   # <-- kept so skill extraction works
        "contract_type": job.get("contract_type"),
        "created": job.get("created"),
        "redirect_url": job.get("redirect_url"),
        "search_role": role,                     # which query found this posting
        "pull_date": datetime.now().date().isoformat(),
    }


def main():
    app_id, app_key = get_credentials()
    rows = []

    for role in ROLES:
        print(f"Fetching: {role}")
        for page in range(1, PAGES_PER_ROLE + 1):
            results = fetch_page(app_id, app_key, role, page)
            if results is None:      # HTTP error — move to next role
                break
            if not results:          # no more results for this role
                print(f"    (no more results after page {page - 1})")
                break
            rows.extend(parse_job(j, role) for j in results)
            print(f"    page {page}: {len(results)} postings (running total {len(rows)})")
            time.sleep(SLEEP_SECONDS)

    if not rows:
        raise SystemExit("No data returned. Check your API keys and internet connection.")

    df = pd.DataFrame(rows).drop_duplicates(subset="id").reset_index(drop=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"jobs_raw_{stamp}.csv"
    df.to_csv(out_path, index=False)

    print("\n" + "=" * 50)
    print(f"DONE. {len(df)} unique postings saved to {out_path}")
    print(f"Salary present: {df['salary_min'].notna().sum()} of {len(df)}")
    print(f"Descriptions present: {df['description'].notna().sum()} of {len(df)}")
    print("=" * 50)


if __name__ == "__main__":
    main()

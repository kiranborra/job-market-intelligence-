"""
fetch_jobs.py
-------------
Day 1 script: pulls job listings from the Adzuna API and saves them
as a timestamped raw CSV in the data/ folder.

Run this with: python scripts/fetch_jobs.py
"""

import os
import csv
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")
COUNTRY = os.getenv("ADZUNA_COUNTRY", "in")
QUERY = os.getenv("SEARCH_QUERY", "data analyst")
RESULTS_COUNT = int(os.getenv("RESULTS_COUNT", "50"))

BASE_URL = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"

FIELDS = [
    "id", "title", "company", "location", "category",
    "salary_min", "salary_max", "contract_type", "created",
    "description", "redirect_url",
]


def fetch_jobs():
    if not APP_ID or not APP_KEY or APP_ID == "your_app_id_here":
        raise SystemExit(
            "ERROR: Missing Adzuna API credentials.\n"
            "Check your .env file has real ADZUNA_APP_ID and ADZUNA_APP_KEY values."
        )

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": min(RESULTS_COUNT, 50),
        "what": QUERY,
        "content-type": "application/json",
    }

    print(f"Fetching jobs for '{QUERY}' in country '{COUNTRY}'...")
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])
    print(f"Received {len(results)} job listings.")

    return results


def save_raw_csv(results):
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"data/jobs_raw_{timestamp}.csv"

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()

        for job in results:
            row = {
                "id": job.get("id"),
                "title": job.get("title"),
                "company": job.get("company", {}).get("display_name"),
                "location": job.get("location", {}).get("display_name"),
                "category": job.get("category", {}).get("label"),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "contract_type": job.get("contract_type"),
                "created": job.get("created"),
                "description": job.get("description"),
                "redirect_url": job.get("redirect_url"),
            }
            writer.writerow(row)

    print(f"Saved raw data to {filepath}")
    return filepath


if __name__ == "__main__":
    results = fetch_jobs()
    if results:
        save_raw_csv(results)
    else:
        print("No results returned. Try a broader SEARCH_QUERY in your .env file.")
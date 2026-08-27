# Job Market Intelligence Dashboard

A data pipeline that collects live job market data, cleans it, structures it
into a relational database, and visualizes it in an interactive Power BI
dashboard — built end-to-end using Python, SQL, and Power BI.

## What it does

This project pulls real, live "Data Analyst" job postings from the
[Adzuna API](https://developer.adzuna.com/), cleans and processes the data,
loads it into a SQLite database, and visualizes key hiring trends —
in-demand skills, salary patterns by location, and top hiring companies —
in a Power BI dashboard.

## Dashboard Preview

### Page 1: The Hiring Landscape
*Focuses on seniority, entry-level share, and top employers.*
![Breaking In Dashboard](assets/dashboard-page1.png)

### Page 2: Skill Intelligence
*The Role x Skill Matrix – see which tools unlock which roles.*
![Skill Matrix Dashboard](assets/dashboard-page2.png)

## Key Findings (from a sample of 2,588 live job postings)

- **SQL is the most in-demand skill**, appearing in the majority of listings —
  more than any other single skill, significantly ahead of Python and Excel.
- **Only ~15% of job listings report a specific salary figure**, meaning
  salary-based analysis in this dataset is directional, not comprehensive.
- **The market is highly concentrated**, with a small number of active companies accounting for a disproportionate share of total hiring postings.

## Architecture

```
Adzuna API → Python (fetch + clean) → SQLite database → SQL analysis → Power BI dashboard
```

| Stage | Tool | What happens |
|---|---|---|
| Fetch | Python (`requests`, `python-dotenv`) | Pull live job listings from the Adzuna API |
| Clean | Python (`pandas`, `re`) | Remove duplicates, handle missing salaries honestly (not faked), fix text encoding issues, extract skills via regex keyword matching |
| Store | SQLite | Structured into 3 normalized tables: `jobs`, `skills`, `job_skills` |
| Analyze | SQL | JOINs and GROUP BY queries to answer real hiring questions |
| Visualize | Power BI | Interactive charts: top skills, salary by location, top hiring companies |

## Project Structure

```
job-market-intelligence/
├── assets/             # Dashboard page 1 and 2 screenshots
├── dashboard/          # Power BI report (.pbix) + CSV exports
├── data/               # Raw & cleaned CSVs + the SQLite database
├── scripts/            # fetch_jobs.py, clean_data.py, load_to_sql.py
├── sql/                # analysis_queries.sql
├── .env.example        # Template for API credentials (never commit the real .env!)
├── requirements.txt
└── README.md
```

## How to run it yourself

1. Clone this repo and create a virtual environment
2. `pip install -r requirements.txt`
3. Get a free API key at [developer.adzuna.com](https://developer.adzuna.com/)
4. Copy `.env.example` to `.env` and add your real API credentials
5. Run the pipeline in order:
   ```
   python scripts/fetch_jobs.py
   python scripts/clean_data.py
   python scripts/load_to_sql.py
   ```
6. Open `data/job_market.db` in DB Browser for SQLite and run the queries
   in `sql/analysis_queries.sql`
7. Open `dashboard/job_market_dashboard.pbix` in Power BI Desktop

## What I learned building this

- Debugged a real false-positive bug in skill-extraction logic (a naive
  substring match on "r" was matching inside words like "reporting" —
  fixed using regex word-boundary matching)
- Practiced handling missing data honestly — choosing to flag missing
  salaries rather than fabricate placeholder values, since fake data
  would have quietly skewed the salary-by-location analysis
- Learned the mechanics of normalized relational schema design (splitting
  skills into their own table rather than storing them as repeated text)
- Got hands-on with the command line for file management, environment
  variables, and running a multi-stage Python pipeline

## Limitations & honest caveats

- Sample size is significant (2,588 postings) but restricted to specific search queries —
  this is a portfolio/demo project, not a comprehensive market study
- Salary data is self-reported by employers on Adzuna and only present
  for a minority of listings
- Skill extraction uses simple keyword matching, not NLP — it will miss
  skills phrased in unusual ways

## Tech Stack

Python (pandas, requests) · SQL (SQLite) · Power BI (DAX) · Git

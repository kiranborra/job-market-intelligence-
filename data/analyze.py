"""
analyze.py — Step 3b: run every query in queries.sql and print the results.

This is the script that produces the numbers for your README's "Key Findings"
section, so you never have to hand-copy a figure and risk it going stale.

It parses queries.sql into named blocks ("-- name: ..."), runs each against
job_market.db, prints the result as a table, and finishes with a ready-to-paste
Key Findings summary.

HOW TO RUN
----------
    python analyze.py            # print everything
    python analyze.py --save     # also write analysis_output.txt
"""

import os
import re
import sqlite3
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "job_market.db")
SQL_PATH = os.path.join(HERE, "queries.sql")


def parse_queries(path):
    """Split queries.sql into (name, sql) pairs on '-- name:' markers."""
    text = open(path, encoding="utf-8").read()
    blocks = re.split(r"^--\s*name:\s*(.+)$", text, flags=re.MULTILINE)
    # blocks[0] is the file header/comment before the first marker
    out = []
    for i in range(1, len(blocks), 2):
        name = blocks[i].strip()
        sql = blocks[i + 1].strip()
        sql = re.sub(r"^--.*$", "", sql, flags=re.MULTILINE).strip()  # drop comments
        if sql:
            out.append((name, sql))
    return out


def key_findings(con):
    """Compute the handful of numbers that go at the top of the README."""
    q = lambda s: con.execute(s).fetchone()

    total, companies, earliest, latest = q(
        "SELECT COUNT(*), COUNT(DISTINCT company), MIN(posted_date), MAX(posted_date) FROM jobs")
    entry, pct_entry = q("""
        SELECT SUM(CASE WHEN seniority IN ('Junior / Entry','Intern / Trainee') THEN 1 ELSE 0 END),
               ROUND(100.0*SUM(CASE WHEN seniority IN ('Junior / Entry','Intern / Trainee')
                                    THEN 1 ELSE 0 END)/COUNT(*),1)
        FROM jobs""")
    top3_pct = q("""
        SELECT ROUND(SUM(pct_of_located),1) FROM (
            SELECT pct_of_located FROM v_city_demand ORDER BY job_count DESC LIMIT 3)""")[0]
    top_city, top_city_pct = q(
        "SELECT city, pct_of_located FROM v_city_demand ORDER BY job_count DESC LIMIT 1")
    top_co, top_co_n, top_co_pct = q(
        "SELECT company, job_count, pct_of_postings FROM v_top_companies ORDER BY job_count DESC LIMIT 1")
    coverage = q("""
        SELECT ROUND(100.0*COUNT(DISTINCT job_id)/(SELECT COUNT(*) FROM jobs),0)
        FROM job_skills""")[0]

    sig = con.execute("""
        SELECT role_group, skill_name, pct_of_role FROM v_skill_by_role vr
        WHERE pct_of_role = (SELECT MAX(pct_of_role) FROM v_skill_by_role x
                             WHERE x.role_group = vr.role_group)
        ORDER BY pct_of_role DESC""").fetchall()

    lines = []
    add = lines.append
    add("=" * 72)
    add("KEY FINDINGS  (paste these into the README)")
    add("=" * 72)
    add(f"Dataset: {total:,} live postings from {companies:,} companies, "
        f"posted {earliest} to {latest}.")
    add("")
    add(f"1. Entry-level roles are scarce. Only {entry} of {total:,} postings "
        f"({pct_entry}%) are junior, graduate or internship level. The rest ask "
        f"for mid-level experience or above.")
    add("")
    add(f"2. Hiring is concentrated in a few cities. The top three account for "
        f"{top3_pct}% of postings that name a city, with {top_city} alone at "
        f"{top_city_pct}%.")
    add("")
    add(f"3. A single employer dominates. {top_co} posted {top_co_n} roles "
        f"({top_co_pct}% of the market).")
    add("")
    add("4. Each role family has a signature tool:")
    for role, skill, pct in sig:
        add(f"     {role:<24} {skill} ({pct}% of its postings)")
    add("")
    add(f"   So what: the five job titles are not interchangeable. Applying to "
        f"'data roles' generically wastes effort - the tool you learn should "
        f"follow the role you target.")
    add("")
    add(f"Method note: skills were detected in {coverage:.0f}% of postings. The "
        f"Adzuna API truncates descriptions to ~500 characters, so absolute "
        f"percentages understate demand; comparisons between roles are the "
        f"reliable signal.")
    add("=" * 72)
    return "\n".join(lines)


def main():
    if not os.path.exists(DB_PATH):
        raise SystemExit("job_market.db not found — run load_db.py first.")

    con = sqlite3.connect(DB_PATH)
    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", 30)

    chunks = []
    for name, sql in parse_queries(SQL_PATH):
        try:
            df = pd.read_sql_query(sql, con)
        except Exception as e:
            chunks.append(f"\n### {name}\n  QUERY FAILED: {e}")
            continue
        body = df.to_string(index=False) if len(df) else "  (no rows)"
        chunks.append(f"\n### {name}\n{body}")

    findings = key_findings(con)
    report = "\n".join(chunks) + "\n\n" + findings

    print(report)

    if "--save" in sys.argv:
        out = os.path.join(HERE, "analysis_output.txt")
        open(out, "w", encoding="utf-8").write(report)
        print(f"\nsaved to {os.path.basename(out)}")

    con.close()


if __name__ == "__main__":
    main()

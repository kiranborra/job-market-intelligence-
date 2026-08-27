-- queries.sql — the analysis behind the dashboard, as reviewable SQL.
--
-- Each block starts with "-- name: <title>" so analyze.py can run them all and
-- print the results. Keeping the SQL in a file (rather than only inside Power BI)
-- means anyone reviewing this repo can actually see the analytical work.
--
-- IMPORTANT CAVEAT carried through all skill queries: the Adzuna search API
-- truncates job descriptions to ~500 characters, so skill percentages measure
-- what employers mention EARLY in a posting, not everything they require.
-- Absolute percentages understate demand; comparisons BETWEEN roles are the
-- trustworthy signal because truncation applies to every role equally.


-- name: Dataset summary
SELECT COUNT(*)                                        AS postings,
       COUNT(DISTINCT company)                         AS companies,
       COUNT(DISTINCT city)                            AS cities,
       MIN(posted_date)                                AS earliest,
       MAX(posted_date)                                AS latest,
       SUM(salary_reported)                            AS with_salary,
       SUM(description_truncated)                      AS truncated_descriptions
FROM jobs;


-- name: Seniority mix (the headline finding)
SELECT seniority, job_count, pct_of_postings
FROM v_seniority_mix
ORDER BY job_count DESC;


-- name: Entry-level share of the market
SELECT SUM(CASE WHEN seniority IN ('Junior / Entry','Intern / Trainee')
                THEN 1 ELSE 0 END)                                  AS entry_level_jobs,
       COUNT(*)                                                     AS all_jobs,
       ROUND(100.0 * SUM(CASE WHEN seniority IN ('Junior / Entry','Intern / Trainee')
                              THEN 1 ELSE 0 END) / COUNT(*), 1)     AS pct_entry_level
FROM jobs;


-- name: Which role families have any entry-level openings
SELECT role_group,
       COUNT(*)                                                          AS total_jobs,
       SUM(CASE WHEN seniority IN ('Junior / Entry','Intern / Trainee')
                THEN 1 ELSE 0 END)                                       AS entry_jobs,
       ROUND(100.0 * SUM(CASE WHEN seniority IN ('Junior / Entry','Intern / Trainee')
                              THEN 1 ELSE 0 END) / COUNT(*), 1)          AS pct_entry
FROM jobs
GROUP BY role_group
ORDER BY pct_entry DESC;


-- name: Top 15 skills mentioned overall
SELECT skill_name, skill_category, job_count, pct_of_postings
FROM v_skill_demand
ORDER BY job_count DESC
LIMIT 15;


-- name: Skill mix by role family (the actionable matrix)
SELECT skill_name,
       MAX(CASE WHEN role_group='Data Analyst'          THEN pct_of_role END) AS data_analyst,
       MAX(CASE WHEN role_group='Business Analyst'      THEN pct_of_role END) AS business_analyst,
       MAX(CASE WHEN role_group='Business Intelligence' THEN pct_of_role END) AS bi,
       MAX(CASE WHEN role_group='Data Engineer'         THEN pct_of_role END) AS data_engineer,
       MAX(CASE WHEN role_group='Data Scientist'        THEN pct_of_role END) AS data_scientist
FROM v_skill_by_role
GROUP BY skill_name
HAVING COALESCE(data_analyst,0) + COALESCE(business_analyst,0) + COALESCE(bi,0)
     + COALESCE(data_engineer,0) + COALESCE(data_scientist,0) > 8
ORDER BY skill_name;


-- name: The signature skill of each role family
SELECT role_group, skill_name, pct_of_role
FROM v_skill_by_role vr
WHERE pct_of_role = (SELECT MAX(pct_of_role) FROM v_skill_by_role x
                     WHERE x.role_group = vr.role_group)
ORDER BY pct_of_role DESC;


-- name: Geographic concentration
SELECT city, job_count, pct_of_located
FROM v_city_demand
ORDER BY job_count DESC
LIMIT 10;


-- name: Top 10 hiring companies
SELECT company, job_count, cities, pct_of_postings
FROM v_top_companies
ORDER BY job_count DESC
LIMIT 10;


-- name: What entry-level postings ask for
SELECT skill_name, job_count, pct_of_entry
FROM v_entry_level_skills
ORDER BY job_count DESC
LIMIT 10;


-- name: Posting volume by week
SELECT posted_week, SUM(job_count) AS job_count
FROM v_weekly_postings
GROUP BY posted_week
ORDER BY posted_week;


-- name: Salary where reported (small sample - treat with caution)
SELECT role_group,
       COUNT(*)                    AS jobs_with_salary,
       ROUND(MIN(salary_lpa), 1)   AS min_lpa,
       ROUND(AVG(salary_lpa), 1)   AS avg_lpa,
       ROUND(MAX(salary_lpa), 1)   AS max_lpa
FROM jobs
WHERE salary_reported = 1
GROUP BY role_group
ORDER BY avg_lpa DESC;

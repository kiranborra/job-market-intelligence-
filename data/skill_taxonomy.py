"""
skill_taxonomy.py — the vocabulary used to detect skills in job descriptions.

This is DATA, not logic. Keeping it in its own file means you can add a skill
without touching the extraction code, which is also easier to defend in an
interview ("the taxonomy is curated and version-controlled, separate from the
matching logic").

WHY THIS FILE EXISTS
--------------------
The first version of this project tagged a skill only when it appeared in the
short job TITLE, so just 27% of postings got any skill at all. This taxonomy is
matched against the job DESCRIPTION instead, with word boundaries and alias
handling, which lifts coverage dramatically.

STRUCTURE
---------
SKILLS maps a canonical skill name -> (category, [aliases to search for]).
The canonical name is what shows up in the dashboard. Aliases capture the many
ways employers write the same thing ("power bi", "powerbi", "pbi").
"""

# category -> used for grouping in the dashboard (e.g. "which BI tools dominate?")
SKILLS = {
    # ---------------- Programming & querying ----------------
    "SQL":              ("Programming & Query", ["sql", "t-sql", "tsql", "pl/sql", "plsql", "mysql", "postgresql", "ms sql"]),
    "Python":           ("Programming & Query", ["python", "pandas", "numpy"]),
    # "R" is a single letter, which makes naive matching dangerous. A plain \br\b
    # matched things like the requisition ID "R-801324". So we only accept R when
    # it appears in a genuine programming context: named as a language, or listed
    # alongside another language. This trades a little recall for a lot of trust.
    "R":                ("Programming & Query", [
        r"\br\s+(?:programming|language|studio|shiny|script)\b",
        r"\b(?:python|sql|sas|scala|java|excel|tableau|spss)\s*(?:,|/|\bor\b|\band\b)\s*r\b(?![-\w…])",
        r"\br\s*(?:,|/)\s*(?:python|sql|sas|tableau|excel)\b",
        r"\b(?:in|using|with)\s+r\b(?![-\w…])",
        r"\br\s+for\s+(?:data|statistical|analysis|analytics)\b",
    ]),
    "SAS":              ("Programming & Query", ["sas"]),
    "Scala":            ("Programming & Query", ["scala"]),
    # plain "java" is safe: the auto-added \bjava\b will not match "javascript",
    # because \b requires a non-word character after "java".
    "Java":             ("Programming & Query", ["java"]),
    "VBA / Macros":     ("Programming & Query", ["vba", "macros"]),

    # ---------------- BI & visualisation ----------------
    "Power BI":         ("BI & Visualisation", ["power bi", "powerbi", "power-bi", "pbi", "dax", "power query"]),
    "Tableau":          ("BI & Visualisation", ["tableau"]),
    "Excel":            ("BI & Visualisation", ["excel", "vlookup", "pivot table", "pivot tables", "spreadsheet"]),
    "Looker":           ("BI & Visualisation", ["looker", "looker studio", "data studio"]),
    "Qlik":             ("BI & Visualisation", ["qlik", "qlikview", "qliksense"]),
    "SSRS":             ("BI & Visualisation", ["ssrs", "reporting services"]),

    # ---------------- Cloud & data platforms ----------------
    "AWS":              ("Cloud & Platforms", ["aws", "amazon web services", "redshift", "s3 bucket"]),
    "Azure":            ("Cloud & Platforms", ["azure", "synapse", "adf", "azure data factory"]),
    "GCP":              ("Cloud & Platforms", ["gcp", "google cloud", "bigquery", "big query"]),
    "Snowflake":        ("Cloud & Platforms", ["snowflake"]),
    "Databricks":       ("Cloud & Platforms", ["databricks"]),

    # ---------------- Data engineering ----------------
    "ETL":              ("Data Engineering", ["etl", "elt", "data pipeline", "data pipelines"]),
    "Spark":            ("Data Engineering", ["spark", "pyspark"]),
    "Hadoop":           ("Data Engineering", ["hadoop", "hive", "hdfs"]),
    "Kafka":            ("Data Engineering", ["kafka"]),
    "Airflow":          ("Data Engineering", ["airflow"]),
    "dbt":              ("Data Engineering", ["dbt"]),
    "SSIS":             ("Data Engineering", ["ssis"]),
    "Informatica":      ("Data Engineering", ["informatica"]),
    "Data Warehousing": ("Data Engineering", ["data warehouse", "data warehousing", "dwh", "dimensional model", "star schema"]),
    "Data Modeling":    ("Data Engineering", ["data modeling", "data modelling"]),

    # ---------------- Analytics & ML ----------------
    "Statistics":       ("Analytics & ML", ["statistics", "statistical", "hypothesis testing", "regression"]),
    "Machine Learning": ("Analytics & ML", ["machine learning", r"\bml\b", "scikit", "sklearn"]),
    "NLP":              ("Analytics & ML", ["nlp", "natural language processing"]),
    "Deep Learning":    ("Analytics & ML", ["deep learning", "tensorflow", "pytorch", "neural network"]),
    "A/B Testing":      ("Analytics & ML", ["a/b test", "a/b testing", "ab testing", "split test", "experimentation"]),
    "Forecasting":      ("Analytics & ML", ["forecasting", "time series", "predictive model", "predictive modeling"]),

    # ---------------- Business analysis (matters for BA roles) ----------------
    "Requirements Gathering": ("Business Analysis", ["requirement gathering", "requirements gathering", "requirement elicitation", "brd", "frd", "user stories"]),
    "Stakeholder Management": ("Business Analysis", ["stakeholder management", "stakeholder", "stakeholders"]),
    "Process Improvement":    ("Business Analysis", ["process improvement", "business process", "process mapping", "gap analysis"]),
    "UAT":                    ("Business Analysis", ["uat", "user acceptance testing"]),
    "Agile / Scrum":          ("Business Analysis", ["agile", "scrum", "kanban", "sprint"]),
    "Jira":                   ("Business Analysis", ["jira", "confluence"]),
    "KPI / Reporting":        ("Business Analysis", ["kpi", "kpis", "dashboarding", "mis report", "management reporting"]),
    "Data Governance":        ("Business Analysis", ["data governance", "data quality", "data stewardship", "mdm", "master data"]),

    # ---------------- Other tooling ----------------
    "Git":              ("Tooling", ["git", "github", "gitlab", "version control"]),
    "Alteryx":          ("Tooling", ["alteryx"]),
    "SPSS":             ("Tooling", ["spss"]),
}


# Aliases that are already regex (contain \b or lookarounds) are used as-is.
# Everything else gets wrapped in word boundaries by extract_skills.py.
RAW_REGEX_MARKERS = ("\\b", "(?!", "(?=")


def total_skills() -> int:
    return len(SKILLS)


def categories() -> list:
    return sorted({cat for cat, _ in SKILLS.values()})


if __name__ == "__main__":
    print(f"{total_skills()} skills across {len(categories())} categories:")
    for cat in categories():
        names = [k for k, (c, _) in SKILLS.items() if c == cat]
        print(f"  {cat}: {', '.join(sorted(names))}")

# 📊 Job Market Intelligence Dashboard

An end-to-end data pipeline that collects, cleans, and analyzes **2,588 job postings** from the Adzuna API. This project decodes the current Indian data job market to help junior professionals bridge the gap between their skills and industry expectations.

Built with Python, SQL, and Power BI.

---

## 📊 Project Visuals

### Page 1: The Hiring Landscape
*Focuses on seniority, entry-level share, and top employers.*
![Breaking In Dashboard](assets/dashboard-page1.png)

### Page 2: Skill Intelligence
*The Role x Skill Matrix – see which tools unlock which roles.*
![Skill Matrix Dashboard](assets/dashboard-page2.png)

---

## 💡 Why This Project?
The data job market is often opaque. By scraping and analyzing live postings from the Adzuna API, this project identifies:
*   **The "Junior" Barrier:** How few roles are actually entry-level (3.1%).
*   **Role DNA:** Exactly which tools—from ETL to ML—are required for specific career paths.
*   **Market Concentration:** Insights into the top hiring companies and city clusters.

---

## 🚀 Key Insights
| Role Family | Signature Skill | Market Reality |
|---|---|---|
| **Data Engineer** | ETL | Highly specialized; tech-heavy. |
| **Business Intelligence**| Power BI | Driven by reporting efficiency. |
| **Data Scientist** | Machine Learning | High barrier to entry. |
| **Data Analyst** | SQL | The most accessible entry point. |

---

## 🛠 Tech Stack
*   **Data Pipeline:** Python (`pandas`, `requests` for API scraping)
*   **Data Processing:** SQL (`SQLite`) for cleaning & querying
*   **Visualization:** Power BI (DAX, Interactive Dashboards)
*   **Automation:** End-to-end ETL scripts

---

## 💻 How to Run It Yourself

### Prerequisites
*   Python 3.x
*   [Free Adzuna API Key](https://developer.adzuna.com/)

### Steps
1. **Clone the repository:**
   ```bash
   git clone https://github.com/kiranborra/job-market-intelligence.git
   cd job-market-intelligence
   ```
2. **Setup environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Configure:**
   *   Copy `.env.example` to `.env` and add your Adzuna API key.
4. **Execute pipeline:**
   ```bash
   python collect.py
   python clean.py
   python extract_skills.py
   python load_db.py
   python analyze.py
   ```
5. **Visualize:**
   *   Open `dashboard/job_market_dashboard.pbix` in Power BI Desktop to view the reports using the exported CSV files.

---

## ⚠️ Caveats & Insights
*   **API Limits:** Postings are truncated; counts represent "mentioned in posting" (a reliable signal for comparison, not an absolute demand count).
*   **Survivorship Bias:** Posting volume trends include expired listings; the dashboard focuses on fresh hiring data.
*   **Salary Data:** Excluded due to low reporting rates, ensuring the dashboard relies only on high-confidence data.

---

*Built for the Data Analytics Community.*

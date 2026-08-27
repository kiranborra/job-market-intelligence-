# Dashboard build guide

Follow top to bottom. Every expected number is listed so you can catch a mistake
the moment it happens rather than three steps later.

Save first: **Ctrl+S** → `job_market_dashboard.pbix` in the project folder.
The title bar currently says "Untitled", which means nothing is on disk yet.

---

## 0. Fixes to what is already on Page 1

**Delete nothing.** All three charts are correct. Four repairs:

| Problem | Where | Fix |
|---|---|---|
| "Cities" is a **waterfall chart** (Increase/Decrease/Total legend) | select it | Visualizations gallery → click the **Card** icon (the "123" one). Converts in place. |
| Chart 1 still shows the gradient colour scale bottom-left | select chart 1 | Format → **General** tab → **Legend** → Off |
| All three charts show auto-subtitles ("by role_group") | each chart | Format → **General** → **Subtitle** → Off |
| Slicer is oversized and empty | select it | drag `role_group` into it; Format → Slicer settings → Options → **Dropdown** |

**Retitle all three charts.** A title states the finding; the axes already
state the fields.

- Chart 1 → `Only 3% of postings are open to juniors`
- Chart 2 → `Data Analyst is the most accessible entry point`
- Chart 3 → `ETL and Power BI lead, but the mix differs sharply by role`

---

## 1. Three missing cards on Page 1

Click empty canvas → **Card** visual → drag one measure into **Fields**. Repeat.

| Card | Measure | Must read |
|---|---|---|
| Postings analysed | `Total Postings` | 1,569 |
| Entry-level share | `% Entry-Level` | 3.1 |
| Companies hiring | `Companies` | 774 |
| Cities | `Cities` | 81 (already correct) |

On each: Format → **Callout value** → font size 28; **Category label** → On.

Select all four with Ctrl+click, then set identical sizes in the next step.

---

## 2. Two text boxes on Page 1

**Insert ribbon → Text box.**

Title, 28pt bold:

```
Breaking in: only 3.1% of India's data roles are open to juniors
```

Footnote, 9pt grey — this one is not optional:

```
1,569 live postings from Adzuna, 24 May - 23 Aug 2026. Skills detected in 882
postings; the API truncates descriptions to ~500 characters, so skill figures
show what employers mention first and understate true demand. Comparisons
between roles are the reliable signal.
```

Without that footnote the chart overclaims. With it, you look like someone who
understands the limits of their own data — which is the rarer signal.

---

## 3. Page 1 layout

Select a visual → Format pane → **General → Properties → Position**. Type exact
numbers rather than dragging; canvas is 1280 x 720.

| Element | X | Y | Width | Height |
|---|---|---|---|---|
| Title text box | 20 | 15 | 900 | 55 |
| Card: Postings | 20 | 85 | 220 | 90 |
| Card: % Entry-Level | 255 | 85 | 220 | 90 |
| Card: Companies | 490 | 85 | 220 | 90 |
| Card: Cities | 725 | 85 | 220 | 90 |
| Slicer (role_group) | 960 | 85 | 300 | 90 |
| Chart 1 - seniority | 20 | 190 | 610 | 230 |
| Chart 2 - % entry by role | 650 | 190 | 610 | 230 |
| Chart 3 - top 10 skills | 20 | 435 | 900 | 250 |
| Footnote text box | 940 | 435 | 320 | 250 |

Then: Format page → Canvas background → **#F5F5F5**, transparency 0%.
Each visual → Format → General → Effects → Background → **white**.

Rename the page tab (double-click "Page 1") to **Breaking In**.

---

## 4. PAGE 2 — the payoff

Click the **+** next to the page tab. Rename it **What To Learn**.

Page 1 says the door is mostly shut. Page 2 says which key fits which door.
This is the page worth talking about in an interview.

### 4a. The role x skill matrix (the centrepiece)

Visualizations gallery → **Matrix**.

- **Rows**: `skill_name`
- **Columns**: `role_group`
- **Values**: `% Mentioning Skill`

Filters on this visual → `skill_name` → **Top N** → Top **12** → By value
`Postings Mentioning Skill` → Apply.

Then Format → **Cell elements** → Background color → **On** → fx →
Format style **Gradient**, lowest white, highest dark blue.

Title: `Each role family has a signature tool`

Expected values (% of that role's postings):

| Skill | Data Analyst | Business Analyst | BI | Data Engineer | Data Scientist |
|---|---|---|---|---|---|
| ETL | 3.7 | - | 8.8 | **61.3** | 0.7 |
| Data Governance | 6.3 | 1.4 | 5.4 | **41.3** | 1.4 |
| Power BI | 10.9 | 1.4 | **41.3** | 2.9 | 2.2 |
| Machine Learning | 2.9 | 1.8 | 1.9 | 3.7 | **30.9** |
| Stakeholder Mgmt | 11.2 | **26.0** | 11.7 | 2.6 | 4.7 |
| SQL | 17.5 | 3.6 | 17.7 | 13.8 | 3.6 |
| Python | 9.5 | 1.1 | 2.2 | **14.3** | 8.6 |
| Statistics | 7.5 | 2.2 | 0.9 | 0.6 | **13.7** |

Why this matters: ETL is 61.3% for Data Engineer and 0.7% for Data Scientist —
an 87x difference in one row. The five titles are not interchangeable, and
applying to "data roles" generically wastes effort.

It is also a **validity check on the skill extraction**. If the regex were
broken, skills would scatter randomly across columns. Instead every skill lands
in the role you would predict. That is the answer to "how do you know your
matching worked?"

### 4b. Skill-category mix by role

**100% Stacked bar chart.**

- Y-axis: `role_group`
- X-axis: `Postings Mentioning Skill`
- Legend: `skill_category`

Title: `Data Engineer is a platform job; Business Analyst is a people job`

Expected shape — Data Engineer is dominated by Data Engineering (334 pairs) and
Cloud & Platforms (189); Business Analyst is 143 of ~189 pairs Business
Analysis; Data Scientist is 163 Analytics & ML. Data Analyst is the only role
with no dominant block — BI & Visualisation 111, Programming & Query 108,
Business Analysis 76 — i.e. it is the generalist entry point, which is
consistent with it having the highest entry-level share on Page 1.

### 4c. Where the jobs are

**Clustered bar chart.**

- Y-axis: `city`
- X-axis: `Total Postings`
- Filters → `city` → Top N → Top 8 by `Total Postings`
- Filters → `city` → also exclude "Not specified" (Basic filtering, untick it)

Title: `A third of the market is in one city`

Expected: Bangalore 312, Hyderabad 178, Mumbai 86, Pune 86, Chennai 72.
Bangalore is 31.3% of postings that name a city.

### 4d. Who is hiring

**Clustered bar chart**, Y-axis `company`, X-axis `Total Postings`,
Top N = 8 by `Total Postings`.

Title: `One employer posts 1 in 9 roles`

Expected: Accenture 169 (10.8%), EXL 45, Amazon 30, Amgen 26, Kyndryl 23.

Add a small text box: `Accenture alone posts 10.8% of all roles - a single
employer's hiring cycle moves this entire dataset.`

### Page 2 layout

| Element | X | Y | Width | Height |
|---|---|---|---|---|
| Title text box | 20 | 15 | 900 | 55 |
| Matrix (4a) | 20 | 85 | 760 | 400 |
| Category mix (4b) | 800 | 85 | 460 | 400 |
| Cities (4c) | 20 | 500 | 400 | 200 |
| Companies (4d) | 440 | 500 | 400 | 200 |
| Caveat text box | 860 | 500 | 400 | 200 |

Page 2 title text box, 28pt bold:

```
What to learn depends entirely on which door you knock on
```

---

## 5. Charts deliberately NOT built

Keep this list. When an interviewer asks about limitations, this is the answer.

| Not built | Why |
|---|---|
| Weekly posting trend | Rises 4 -> 320 purely because expired listings vanish from the API. That is survivorship bias, not a hiring surge. Plotting it would be a lie. |
| Salary by role | Only 6-7% of postings report salary. Any average is an average of self-selected disclosers. |
| What entry-level postings ask for | Only 20 of the 48 junior postings named any tool; top count was n=5. Too thin to display. |

Three charts the data offered and you declined. Most junior portfolios plot
everything available; knowing what to leave out is the harder skill.

---

## 6. Export and publish

1. **Ctrl+S** — confirm the title bar no longer says "Untitled".
2. Create folder `assets/` in the repo root.
3. **File → Export → Export to PDF** for a full-fidelity copy, and take PNG
   screenshots of each page (Win+Shift+S) saved as `assets/dashboard-page1.png`
   and `assets/dashboard-page2.png`.
4. Optional GIF: record 8-10 seconds using the slicer, save as
   `assets/dashboard-demo.gif`. ScreenToGif is free.
5. README: embed the page-1 PNG immediately under the title, before any prose.
   A recruiter spends ~20 seconds on a repo; the image has to land in the
   first screen.

### Git commands

```bash
cd "C:\Users\Bhargava kumar\OneDrive\Desktop\job-market-intelligence"
git add .
git commit -m "Add two-page Power BI dashboard on 1,569-posting dataset"
git push
```

Before pushing, confirm `.env` is NOT staged:

```bash
git status --short
```

If `.env` appears in that list, stop and tell me. It holds your API key.

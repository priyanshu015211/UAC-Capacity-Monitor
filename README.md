# UAC Program — Capacity Monitor

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red?logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-3F4F75?logo=plotly&logoColor=white)
![Status](https://img.shields.io/badge/Status-Live-brightgreen)
![Internship](https://img.shields.io/badge/Unified%20Mentor-Internship%20Project-orange)

> A live analytics dashboard that turns raw daily headcounts into actionable capacity intelligence for the HHS Unaccompanied Children care program.

**[Open the live dashboard](https://priyanshu-uac-dashboard.streamlit.app)**

---

## What this is

Every day, thousands of children move through a federally mandated care pipeline — from CBP border custody into HHS shelter facilities, and eventually to vetted sponsors. The problem is that the people managing this system have been working off raw spreadsheets with no way to quickly answer questions like:

- Is the system under more stress than last month?
- When did we last hit a dangerous load level?
- Are discharges keeping up with new arrivals?
- How long does a stress period typically last before things improve?

This dashboard answers all of those questions automatically, in real time, from a single CSV file.

---

## What it does

**Processes 1,075 days of operational data** — ingests, validates, cleans, and engineers features from raw daily counts across CBP custody and HHS care facilities.

**Detects 9 capacity stress windows** — automatically identifies periods of 7+ consecutive days where intake exceeded discharges, flags the worst ones, and shows how long each lasted.

**Flags 138 data anomalies** — validates every record against 3 business rules and surfaces violations without removing them, keeping the pipeline transparent.

**Generates reports automatically** — produces a full 8-section research paper and a government-style executive summary directly from the data, downloadable with one click.

**Projects 60 days forward** — linear trend projection on the system load chart gives planners a near-term outlook.

---

## Pipeline

```
Raw CSV
   │
   ├── data_processing.py
   │     ├── Load & parse dates
   │     ├── Reindex to continuous daily range
   │     ├── Forward-fill gaps, flag imputed rows
   │     ├── Validate business rules, flag anomalies
   │     └── Engineer derived metrics + rolling stats
   │
   ├── metrics.py
   │     ├── Compute 10+ KPIs
   │     ├── Detect stress windows & relief periods
   │     ├── Generate narrative insights
   │     ├── Generate executive summary
   │     └── Generate full research paper
   │
   └── dashboard.py
         ├── 10 KPI cards (2 rows)
         ├── 8+ interactive Plotly charts
         ├── 6-tab Streamlit layout
         ├── Date range, granularity & metric filters
         └── Download buttons (report, exec summary, CSV)
```

---

## Dashboard tabs

| Tab | What you'll find |
|---|---|
| **System overview** | Total load over time with 7/14-day rolling averages, 60-day projection, volatility chart, monthly heatmap |
| **CBP vs. HHS** | Side-by-side census comparison, 30-day discharge ratio, stacked area chart |
| **Intake and backlog** | Red/green daily intake bars, cumulative backlog accumulation |
| **Metric comparison** | Overlay any combination of metrics, summary stats table |
| **Findings** | Auto-generated insights, early vs late bar chart, stress & relief period tables, executive summary, downloads |
| **Data quality** | Validation report, anomaly records, imputed rows calendar, raw data with CSV export |

---

## Key metrics computed

| Metric | Formula |
|---|---|
| Total System Load | CBP Custody + HHS Care |
| Net Daily Intake | Transfers into HHS − Discharges |
| Care Load Growth Rate | Day-over-day % change |
| Backlog Indicator | Cumulative positive net intake |
| Discharge Offset Ratio | Total Discharged ÷ Total Transferred |
| Volatility Index | 7-day rolling std dev as % of mean |
| MA-7 / MA-14 | 7 and 14-day moving averages |

---

## Run it locally

```bash
git clone https://github.com/priyanshu015211/UAC-Capacity-Monitor.git
cd UAC-Capacity-Monitor
pip install -r requirements.txt
streamlit run dashboard.py
```

---

## Stack

| Tool | Why |
|---|---|
| Streamlit | Dashboard framework |
| Pandas | Data processing and resampling |
| NumPy | Numerical operations |
| Plotly | Interactive charts |

---

## Data

HHS Unaccompanied Children Program — Daily Monitoring Reports (2023–2025)  
Dataset provided by Unified Mentor as part of the Data Analytics Internship program.

---

*Built during a Data Analytics internship at Unified Mentor · April 2026*
*Built as part of a Data Analytics internship at Unified Mentor · April 2026*

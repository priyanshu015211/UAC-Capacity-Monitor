# UAC Program — Capacity Monitor

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red?logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-3F4F75?logo=plotly&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-1.24%2B-013243?logo=numpy&logoColor=white)
![Status](https://img.shields.io/badge/Status-Live-brightgreen)
![Internship](https://img.shields.io/badge/Unified%20Mentor-Internship%20Project-orange)

> A production-ready analytics dashboard that turns raw daily headcounts into actionable capacity intelligence for the HHS Unaccompanied Children care program.

**[Open the live dashboard →](https://priyanshu-uac-dashboard.streamlit.app)**

---

## Table of Contents

- [What this is](#what-this-is)
- [Background](#background)
- [Problem Statement](#problem-statement)
- [What it does — by the numbers](#what-it-does--by-the-numbers)
- [Pipeline Architecture](#pipeline-architecture)
- [Project Structure](#project-structure)
- [Dashboard Overview](#dashboard-overview)
- [KPIs and Metrics](#kpis-and-metrics)
- [Validation Rules](#validation-rules)
- [Quick Start](#quick-start)
- [Module Reference](#module-reference)
- [Dependencies](#dependencies)
- [Data Source](#data-source)

---

## What this is

Every day, thousands of children move through a federally mandated care pipeline — from CBP border custody into HHS shelter facilities, and eventually to vetted sponsors. The people managing this system have been working off raw spreadsheets with no way to quickly answer questions like:

- Is the system under more stress than last month?
- When did we last hit a dangerous load level?
- Are discharges keeping up with new arrivals?
- How long does a stress period typically last before things improve?

This dashboard answers all of those questions automatically, in real time, from a single CSV file. It processes 1,075 days of operational data, detects stress windows, flags anomalies, and generates a full research paper and executive summary — all without any manual intervention.

---

## Background

The Unaccompanied Alien Children (UAC) Program is a federally mandated initiative under which children apprehended by U.S. Customs and Border Protection (CBP) are transferred to the Department of Health and Human Services (HHS) for medical screening, shelter, and eventual placement with vetted sponsors.

From a healthcare systems perspective, this program operates as a dynamic care pipeline:

```
Apprehension → CBP Custody → Transfer to HHS → Care & Support → Discharge to Sponsor
```

Effective management of this pipeline requires continuous capacity awareness especially during sudden influxes that risk overcrowding and delayed care.

---

## Problem Statement

Although daily operational data is collected, HHS lacks a centralized analytical framework to assess:

- Total care system load at any point in time
- Balance between inflow and outflow across the pipeline
- Periods of capacity stress and relief
- Sustainability of care delivery over time

Without structured analytics, decision-making becomes reactive increasing the risk of overcrowding, delayed care, and strain on healthcare infrastructure.

---

## What it does — by the numbers

| Metric | Value |
|---|---|
| Days of data processed | 1,075 |
| Anomalies detected and flagged | 138 (12.8% of records) |
| Capacity stress windows identified | 9 |
| Longest stress window | 21 consecutive days |
| Relief periods detected | 52 |
| Peak system load | 11,762 children (Dec 20, 2023) |
| Current load (latest date) | 2,502 children |
| Decline from peak | 78.7% |
| Overall daily trend | −7.81 children/day |
| Interactive charts | 8+ |
| Dashboard tabs | 6 |
| KPI cards | 10 |

---

## Pipeline Architecture

```
CSV Data
   │
   ▼
┌──────────────────────────────────┐
│   data_processing.py             │
│                                  │
│  Step 1 — Ingestion              │  ← Load CSV, parse dates, sort chronologically
│  Step 2 — Validation             │  ← 3 business rules, anomaly flagging
│  Step 3 — Feature Engineering    │  ← Derived metrics, 7/14-day rolling stats
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│   metrics.py                     │
│                                  │
│  Step 4 — KPI Calculations       │  ← 10+ KPIs returned as a flat dict
│  Step 5 — Analytical Insights    │  ← Stress windows, relief periods, narratives
│  Step 9 — Research Paper         │  ← 8-section structured paper
│  Step 10 — Executive Summary     │  ← Policy-ready one-page briefing
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│   dashboard.py                   │
│                                  │
│  Step 6 — Visualizations         │  ← 8+ interactive Plotly charts
│  Step 7 — Streamlit App          │  ← 6-tab dashboard, sidebar filters, KPI cards
└──────────────────────────────────┘
```

---

## Project Structure

```
uac-capacity-monitor/
├── dashboard.py                                        # Streamlit app — main entry point
├── data_processing.py                                  # Ingestion, validation, feature engineering
├── metrics.py                                          # KPIs, insights, research paper, exec summary
├── requirements.txt                                    # Python dependencies
├── HHS_Unaccompanied_Alien_Children_Program__1_.csv    # Source data
├── .streamlit/
│   └── config.toml                                     # Forces light theme on all environments
└── README.md
```

---

## Dashboard Overview

The dashboard has a persistent sidebar for filters and 6 tabs for different views of the data.

### Sidebar Controls

| Control | Description |
|---|---|
| Date range | Filter all charts and KPIs to any sub-period |
| Time granularity | Switch between daily, weekly, and monthly aggregation |
| Metrics to compare | Select metrics to overlay in the Metric comparison tab |

### Tabs

| Tab | What you'll find |
|---|---|
| **System overview** | Total load chart with 7/14-day rolling averages, 60-day linear projection, volatility chart, monthly heatmap |
| **CBP vs. HHS** | Side-by-side daily census, 30-day discharge ratio with equilibrium line, stacked area chart |
| **Intake and backlog** | Red/green coded daily net intake bars, cumulative backlog accumulation area chart |
| **Metric comparison** | Custom overlay chart for any selected metrics, summary statistics table |
| **Findings** | Auto-generated narrative insights, early vs late grouped bar chart, stress window and relief period tables, executive summary, downloadable report and exec summary |
| **Data quality** | Validation summary cards, rule violation breakdown, anomaly sample table, imputed rows calendar, raw data expander with CSV export |

### KPI Cards

**At a glance — 6 cards**

| Card | Description |
|---|---|
| Children in care | Total system load at the latest date |
| In HHS facilities | Current HHS care population |
| In CBP custody | Current CBP custody count |
| Discharge ratio | Discharges as a percentage of total transfers |
| Daily trend | Direction and rate of load change (children/day) |
| Stress windows | Count of 7+ consecutive days of rising intake |

**System health indicators — 4 cards**

| Card | Description |
|---|---|
| Volatility index | Standard deviation as % of mean load |
| Backlog accumulation rate | Average daily intake on positive-intake days |
| Net intake pressure (30d) | 30-day rolling average of transfers minus discharges |
| Peak load recorded | Highest single-day system load with date |

---

## KPIs and Metrics

### Derived Metrics

| Metric | Formula |
|---|---|
| Total System Load | CBP Custody + HHS Care |
| Net Daily Intake | CBP Transferred − HHS Discharged |
| Care Load Growth Rate | Day-over-day % change in Total System Load |
| Backlog Indicator | Cumulative sum of positive net intake days |
| MA-7 | 7-day moving average of Total System Load |
| MA-14 | 14-day moving average of Total System Load |
| Rolling Volatility | 7-day rolling standard deviation of Total System Load |
| Discharge Offset Ratio | Total Discharged ÷ Total Transferred |

---

## Validation Rules

Every record is checked against three business rules. Violations are flagged but never removed — they appear in the Data Quality tab so the pipeline stays fully transparent.

| Rule | Flag | Violations found |
|---|---|---|
| `cbp_transfers ≤ cbp_custody` | `TRANSFER>CUSTODY` | 138 |
| `hhs_discharged ≤ hhs_care` | `DISCHARGE>HSSCARE` | 0 |
| No negative values in any column | `NEG:<COLUMN>` | 0 |

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/priyanshu015211/UAC-Capacity-Monitor.git
cd UAC-Capacity-Monitor
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the dashboard

```bash
streamlit run dashboard.py
```

The app auto-detects the CSV in the same directory and loads it on startup. No configuration needed.

---

## Module Reference

### `data_processing.py`

| Function | Description |
|---|---|
| `load_and_preprocess(filepath)` | Load CSV, parse dates, forward-fill gaps, flag imputed rows |
| `validate_data(df)` | Apply 3 business rules, return anomaly DataFrame and validation report |
| `engineer_features(df)` | Compute all derived metrics and rolling statistics |
| `resample_data(df, granularity)` | Resample to daily, weekly, or monthly frequency |
| `run_pipeline(filepath)` | Run full Steps 1–3 in one call, return all artefacts |

### `metrics.py`

| Function | Description |
|---|---|
| `compute_kpis(df)` | Compute all KPIs as a flat dictionary |
| `generate_insights(df, kpis)` | Detect stress windows, relief periods, high-load periods, narrative bullets |
| `generate_executive_summary(kpis, insights)` | Concise policy-ready briefing |
| `generate_research_paper(df, kpis, insights)` | Full 8-section research paper in Markdown |

### `dashboard.py`

| Component | Description |
|---|---|
| `load_data(filepath)` | Cached pipeline runner — runs once, cached for session |
| `chart_system_load(df, kpis)` | System load with rolling averages and 60-day projection |
| `chart_cbp_vs_hhs(df, kpis)` | Dual line comparison with HHS peak annotation |
| `chart_net_intake(df, kpis)` | Color-coded daily net intake bar chart |
| `chart_backlog(df, kpis)` | Cumulative backlog area chart with peak annotation |
| `chart_discharge_ratio(df, kpis)` | 30-day rolling discharge ratio with 100% equilibrium line |
| `chart_volatility(df, kpis)` | Dual-axis volatility vs system load |
| `chart_monthly_heatmap(df)` | Year × month average load heatmap |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥ 1.32.0 | Dashboard framework |
| `pandas` | ≥ 2.0.0 | Data manipulation and resampling |
| `numpy` | ≥ 1.24.0 | Numerical operations |
| `plotly` | ≥ 5.18.0 | Interactive visualizations |

---

## Data Source

HHS Unaccompanied Children Program — Daily Monitoring Reports (2023–2025)  
Dataset provided by Unified Mentor as part of the Data Analytics Internship program.

---

*Built during a Machine Learning internship at Unified Mentor · April 2026*

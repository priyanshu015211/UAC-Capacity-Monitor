# UAC Program — Capacity Monitor

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red?logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-3F4F75?logo=plotly&logoColor=white)
![Status](https://img.shields.io/badge/Status-Live-brightgreen)
![Internship](https://img.shields.io/badge/Unified%20Mentor-Internship%20Project-orange)

A production-ready analytics dashboard for monitoring healthcare system capacity in the U.S. HHS Unaccompanied Children (UAC) program. Built on real operational data from 2023 to 2025, it tracks daily care load across CBP and HHS facilities, measures intake and discharge flow, detects capacity stress periods, and generates automated insights and policy-ready reports.

**Live demo:** [priyanshu-uac-dashboard.streamlit.app](https://priyanshu-uac-dashboard.streamlit.app)

---

## Table of Contents

- [Background](#background)
- [Problem Statement](#problem-statement)
- [Pipeline Architecture](#pipeline-architecture)
- [Project Structure](#project-structure)
- [Dashboard Overview](#dashboard-overview)
- [KPIs and Metrics](#kpis-and-metrics)
- [Quick Start](#quick-start)
- [Module Reference](#module-reference)
- [Validation Rules](#validation-rules)
- [Dependencies](#dependencies)
- [Data Source](#data-source)

---

## Background

The Unaccompanied Alien Children (UAC) Program is a federally mandated initiative under which children apprehended by U.S. Customs and Border Protection (CBP) are transferred to the Department of Health and Human Services (HHS) for medical screening, shelter, and eventual placement with vetted sponsors.

From a healthcare systems perspective, this program operates as a dynamic care pipeline:

```
Apprehension → CBP Custody → Transfer to HHS → Care & Support → Discharge to Sponsor
```

Effective management of this pipeline requires continuous capacity awareness — especially during sudden influxes that risk overcrowding and delayed care.

---

## Problem Statement

Although daily operational data is collected, HHS lacks a centralized analytical framework to assess:

- Total care system load at any point in time
- Balance between inflow and outflow across the pipeline
- Periods of capacity stress and relief
- Sustainability of care delivery over time

Without structured analytics, decision-making becomes reactive — increasing the risk of overcrowding, delayed care, and strain on healthcare infrastructure.

---

## Pipeline Architecture

```
CSV Data
   │
   ▼
┌─────────────────────────────┐
│   data_processing.py        │
│                             │
│  Step 1: Ingestion          │  ← Load, parse dates, sort, reindex
│  Step 2: Validation         │  ← Business rules, anomaly flagging
│  Step 3: Feature Engineering│  ← Derived metrics, rolling stats
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   metrics.py                │
│                             │
│  Step 4: KPI Calculations   │  ← 10+ KPIs as a dictionary
│  Step 5: Analytical Insights│  ← Stress windows, relief periods
│  Step 9: Research Paper     │  ← 8-section structured paper
│  Step 10: Exec Summary      │  ← Policy-ready briefing
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   dashboard.py              │
│                             │
│  Step 6: Visualizations     │  ← 8+ interactive Plotly charts
│  Step 7: Streamlit App      │  ← 6-tab dashboard, filters, KPI cards
└─────────────────────────────┘
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

The dashboard is organized into 6 tabs with a persistent sidebar for filters.

### Sidebar Controls

| Control | Description |
|---|---|
| Date range | Filter all charts and KPIs to any sub-period |
| Time granularity | Switch between daily, weekly, and monthly views |
| Metrics to compare | Select metrics to overlay in the Metric comparison tab |

### Tabs

| Tab | Contents |
|---|---|
| **System overview** | Total system load chart with 7/14-day rolling averages, 60-day linear projection, volatility chart, monthly heatmap |
| **CBP vs. HHS** | Dual line chart comparing CBP custody and HHS care, 30-day discharge ratio, stacked area chart |
| **Intake and backlog** | Daily net intake bar chart (red/green coded), cumulative backlog accumulation |
| **Metric comparison** | Custom overlay chart for selected metrics with summary statistics table |
| **Findings** | Auto-generated narrative insights, early vs late period comparison, stress windows, relief periods, executive summary, research paper download |
| **Data quality** | Validation summary cards, rule violation table, anomaly sample, imputed rows calendar, raw data expander |

### KPI Cards

**At a glance**

| Card | Description |
|---|---|
| Children in care | Total system load at latest date |
| In HHS facilities | Current HHS care population |
| In CBP custody | Current CBP custody count |
| Discharge ratio | Discharges as a percentage of transfers |
| Daily trend | Direction and rate of system load change |
| Stress windows | Count of 7+ consecutive days of rising intake |

**System health indicators**

| Card | Description |
|---|---|
| Volatility index | Standard deviation as % of mean load |
| Backlog accumulation rate | Avg daily intake on positive-intake days |
| Net intake pressure (30d) | 30-day average of transfers minus discharges |
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

The app will auto-detect the CSV in the same directory and load it on startup.

---

## Module Reference

### `data_processing.py`

| Function | Description |
|---|---|
| `load_and_preprocess(filepath)` | Load CSV, parse dates, forward-fill gaps, flag imputed rows |
| `validate_data(df)` | Apply 3 business rules, return anomaly DataFrame and validation report |
| `engineer_features(df)` | Compute derived metrics and rolling statistics |
| `resample_data(df, granularity)` | Resample to daily, weekly, or monthly frequency |
| `run_pipeline(filepath)` | Full Steps 1–3 pipeline in one call |

### `metrics.py`

| Function | Description |
|---|---|
| `compute_kpis(df)` | Compute all KPIs as a flat dictionary |
| `generate_insights(df, kpis)` | Detect stress windows, relief periods, high-load periods, generate narrative bullets |
| `generate_executive_summary(kpis, insights)` | Concise policy-ready briefing |
| `generate_research_paper(df, kpis, insights)` | Full 8-section research paper in Markdown |

### `dashboard.py`

| Component | Description |
|---|---|
| `load_data(filepath)` | Cached pipeline runner |
| `chart_system_load(df, kpis)` | System load with rolling averages and 60-day projection |
| `chart_cbp_vs_hhs(df, kpis)` | Dual line comparison with peak annotation |
| `chart_net_intake(df, kpis)` | Color-coded daily intake bar chart |
| `chart_backlog(df, kpis)` | Cumulative backlog area chart |
| `chart_discharge_ratio(df, kpis)` | 30-day rolling discharge ratio with equilibrium line |
| `chart_volatility(df, kpis)` | Dual-axis volatility vs system load |
| `chart_monthly_heatmap(df)` | Year × month average load heatmap |

---

## Validation Rules

All records are checked against three business rules. Violations are flagged but not removed — they appear in the Data Quality tab for full transparency.

| Rule | Flag |
|---|---|
| `cbp_transfers ≤ cbp_custody` | `TRANSFER>CUSTODY` |
| `hhs_discharged ≤ hhs_care` | `DISCHARGE>HSSCARE` |
| No negative values in any column | `NEG:<COLUMN>` |

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

U.S. Department of Health and Human Services — Office of Refugee Resettlement  
HHS Unaccompanied Children Program Daily Monitoring Reports (2023–2025)

---

*Built as part of a Data Analytics internship at Unified Mentor · April 2026*

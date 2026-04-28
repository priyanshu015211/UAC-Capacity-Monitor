# UAC Healthcare Analytics Dashboard

**Production-ready analytics pipeline and Streamlit dashboard for monitoring the HHS Unaccompanied Children (UAC) program healthcare capacity.**

---

## 📁 Project Structure

```
uac_dashboard/
├── dashboard.py          # Streamlit dashboard (main entry point)
├── data_processing.py    # Data ingestion, validation, feature engineering
├── metrics.py            # KPI calculations, insights, research paper generation
├── requirements.txt      # Python dependencies
└── README.md
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the dashboard
```bash
# Place your CSV in the same directory, then:
streamlit run dashboard.py

# Or specify a custom data path via environment variable:
UAC_DATA_PATH=/path/to/data.csv streamlit run dashboard.py
```

### 3. Use the file uploader
The dashboard sidebar includes a CSV file uploader — drag and drop your data directly.

---

## 📊 Dashboard Sections

| Section | Description |
|---------|-------------|
| **KPI Cards** | 6 real-time KPIs: Total Under Care, Net Intake Pressure, Peak Load, Volatility, Discharge Offset, HHS Utilisation |
| **System Load Overview** | Total load time-series with rolling average bands and volatility chart |
| **CBP vs HHS Comparison** | Dual-axis comparison of custody vs care populations + discharge offset ratio |
| **Net Intake & Backlog** | Daily intake bar chart (red/green coded) + 30-day backlog accumulation |
| **Insights Panel** | Auto-generated text insights + stress/relief window tables |
| **Data Quality Report** | Validation summary, anomaly flagging, missing data stats |
| **Executive Summary** | Auto-generated executive briefing |
| **Research Paper** | Structured research paper with policy recommendations |
| **Raw Data** | Filterable processed data table with CSV export |

---

## 🔧 Module Reference

### `data_processing.py`
| Function | Description |
|----------|-------------|
| `load_and_preprocess(filepath)` | Load CSV, parse dates, forward-fill gaps, flag imputed rows |
| `validate_data(df)` | Apply 3 business rules, return anomaly DataFrame + validation report |
| `engineer_features(df)` | Compute 8 derived metrics + 3 rolling statistics |
| `run_pipeline(filepath)` | Full pipeline in one call |

### `metrics.py`
| Function | Description |
|----------|-------------|
| `compute_kpis(df)` | Compute 15 KPIs as a dictionary |
| `detect_stress_windows(df)` | Find sustained ≥7-day positive intake streaks |
| `detect_relief_periods(df)` | Find sustained ≥3-day negative intake streaks |
| `detect_high_load_periods(df)` | Return top-decile load records |
| `generate_text_insights(df, kpis)` | Auto-generate 9 insight strings |
| `generate_summary_statistics(df)` | Descriptive statistics for all metrics |
| `generate_research_paper(df, kpis)` | 8-section research paper content |
| `generate_executive_summary(df, kpis)` | Concise executive briefing |

---

## 📐 Derived Metrics

| Metric | Formula |
|--------|---------|
| Total System Load | CBP Custody + HHS Care |
| Net Daily Intake | CBP Transferred − HHS Discharged |
| Care Load Growth Rate | Day-over-day % change in Total System Load |
| Backlog Indicator | 30-day rolling sum of positive net intake |
| MA-7 | 7-day moving average of Total System Load |
| MA-14 | 14-day moving average of Total System Load |
| Rolling Volatility | 7-day rolling standard deviation |
| Discharge Offset Ratio | HHS Discharged ÷ CBP Transferred |

---

## ✅ Validation Rules

1. `cbp_transferred ≤ cbp_custody` — Transfers cannot exceed children in CBP custody
2. `hhs_discharged ≤ hhs_care` — Discharges cannot exceed children in HHS care
3. No negative values in any numeric column

---

## 🎛 Filters

- **Date Range** — Slider to focus on any sub-period
- **Time Granularity** — Daily / Weekly / Monthly resampling
- **Metric Selector** — Focus KPI calculations on selected metrics

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | Dashboard framework |
| `pandas` | Data manipulation |
| `numpy` | Numerical operations |
| `plotly` | Interactive visualisations |

---

*UAC Analytics Engine · Data source: HHS Unaccompanied Children Program Daily Monitoring Reports*

"""
metrics.py
==========
UAC Healthcare System Capacity Analytics Pipeline
Step 4-5 + 9-10: KPI Calculations, Analytical Insights,
                 Research Paper Content, Executive Summary

Author: UAC Analytics Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from datetime import timedelta


# ═══════════════════════════════════════════════════════════════════════════
# STEP 4 — KPI CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════

def compute_kpis(df: pd.DataFrame) -> dict:
    """
    Compute high-level KPIs from the fully processed DataFrame.

    Returns a flat dict suitable for display in dashboard KPI cards.
    """
    df = df.copy()

    # Latest snapshot
    latest = df.sort_values("date").iloc[-1]
    earliest = df.sort_values("date").iloc[0]

    # Total Children Under Care (latest CBP + HHS)
    total_under_care = latest["cbp_custody"] + latest["hhs_care"]

    # Net Intake Pressure: mean net_daily_intake over last 30 days
    last_30 = df[df["date"] >= (latest["date"] - timedelta(days=30))]
    net_intake_pressure = last_30["net_daily_intake"].mean()

    # Care Load Volatility Index: std of system load / mean of system load
    volatility_index = (df["total_system_load"].std() / df["total_system_load"].mean()) * 100

    # Backlog Accumulation Rate: average daily positive intake
    positive_intake_days = df[df["net_daily_intake"] > 0]
    backlog_rate = positive_intake_days["net_daily_intake"].mean() if len(positive_intake_days) > 0 else 0

    # Discharge Offset Ratio: total discharges / total transfers
    total_transfers  = df["cbp_transfers"].sum()
    total_discharged = df["hhs_discharged"].sum()
    discharge_ratio  = (total_discharged / total_transfers) if total_transfers > 0 else 0

    # Peak system load
    peak_load_val  = df["total_system_load"].max()
    peak_load_date = df.loc[df["total_system_load"].idxmax(), "date"]

    # Trough system load
    trough_load_val  = df["total_system_load"].min()
    trough_load_date = df.loc[df["total_system_load"].idxmin(), "date"]

    # Overall trend (linear regression slope on system load)
    x = np.arange(len(df))
    slope = float(np.polyfit(x, df["total_system_load"].ffill(), 1)[0])

    # Average HHS care
    avg_hhs = df["hhs_care"].mean()
    avg_cbp = df["cbp_custody"].mean()

    return {
        # Snapshot KPIs
        "latest_date":              latest["date"].strftime("%Y-%m-%d"),
        "current_total_under_care": int(round(total_under_care)),
        "current_hhs_care":         int(round(latest["hhs_care"])),
        "current_cbp_custody":      int(round(latest["cbp_custody"])),
        # Trend KPIs
        "net_intake_pressure_30d":  round(net_intake_pressure, 2),
        "care_load_volatility_pct": round(volatility_index, 2),
        "backlog_accumulation_rate":round(backlog_rate, 2),
        "discharge_offset_ratio":   round(discharge_ratio, 4),
        # Historical KPIs
        "peak_system_load":         int(round(peak_load_val)),
        "peak_load_date":           peak_load_date.strftime("%Y-%m-%d"),
        "trough_system_load":       int(round(trough_load_val)),
        "trough_load_date":         trough_load_date.strftime("%Y-%m-%d"),
        "avg_hhs_care":             round(avg_hhs, 1),
        "avg_cbp_custody":          round(avg_cbp, 1),
        "overall_load_trend_slope": round(slope, 3),
        "total_days_observed":      len(df),
        "date_range_start":         earliest["date"].strftime("%Y-%m-%d"),
        "date_range_end":           latest["date"].strftime("%Y-%m-%d"),
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 5 — ANALYTICAL INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════

def _find_stress_windows(df: pd.DataFrame, min_consecutive: int = 7) -> list[dict]:
    """Identify sustained positive net-intake windows ≥ min_consecutive days."""
    windows = []
    consecutive = 0
    start_idx = None

    for i, row in df.iterrows():
        if row["net_daily_intake"] > 0:
            if consecutive == 0:
                start_idx = i
            consecutive += 1
        else:
            if consecutive >= min_consecutive:
                windows.append({
                    "start": df.loc[start_idx, "date"],
                    "end":   df.loc[i - 1, "date"],
                    "days":  consecutive,
                    "avg_net_intake": df.loc[start_idx:i-1, "net_daily_intake"].mean(),
                })
            consecutive = 0
            start_idx = None

    # Close any open window
    if consecutive >= min_consecutive:
        last_i = df.index[-1]
        windows.append({
            "start": df.loc[start_idx, "date"],
            "end":   df.loc[last_i, "date"],
            "days":  consecutive,
            "avg_net_intake": df.loc[start_idx:last_i, "net_daily_intake"].mean(),
        })
    return windows


def _find_relief_periods(df: pd.DataFrame, min_consecutive: int = 3) -> list[dict]:
    """Identify consecutive negative net-intake streaks (relief windows)."""
    windows = []
    consecutive = 0
    start_idx = None

    for i, row in df.iterrows():
        if row["net_daily_intake"] < 0:
            if consecutive == 0:
                start_idx = i
            consecutive += 1
        else:
            if consecutive >= min_consecutive:
                windows.append({
                    "start": df.loc[start_idx, "date"],
                    "end":   df.loc[i - 1, "date"],
                    "days":  consecutive,
                    "avg_relief": abs(df.loc[start_idx:i-1, "net_daily_intake"].mean()),
                })
            consecutive = 0
            start_idx = None

    # Close any open window at end of series
    if consecutive >= min_consecutive:
        last_i = df.index[-1]
        windows.append({
            "start": df.loc[start_idx, "date"],
            "end":   df.loc[last_i, "date"],
            "days":  consecutive,
            "avg_relief": abs(df.loc[start_idx:last_i, "net_daily_intake"].mean()),
        })
    return windows


def generate_insights(df: pd.DataFrame, kpis: dict) -> dict:
    """
    Auto-generate analytical insights from the processed data.

    Returns
    -------
    A dict with:
      - high_load_periods   : top-10% load dates
      - stress_windows      : ≥7-day positive intake streaks
      - relief_periods      : negative intake streaks
      - early_vs_late       : trend comparison
      - summary_stats       : describe() dict
      - narrative_bullets   : list of insight strings for the dashboard
    """
    df = df.reset_index(drop=True)

    # ── High-load periods (top 10%) ─────────────────────────────────────────
    threshold_90 = df["total_system_load"].quantile(0.90)
    high_load    = df[df["total_system_load"] >= threshold_90].copy()

    # ── Stress windows ───────────────────────────────────────────────────────
    stress_windows = _find_stress_windows(df, min_consecutive=7)

    # ── Relief periods ───────────────────────────────────────────────────────
    relief_periods = _find_relief_periods(df, min_consecutive=3)

    # ── Early vs late trend ──────────────────────────────────────────────────
    mid  = len(df) // 2
    early_mean = df.iloc[:mid]["total_system_load"].mean()
    late_mean  = df.iloc[mid:]["total_system_load"].mean()
    trend_dir  = "increasing" if late_mean > early_mean else "decreasing"
    trend_pct  = abs((late_mean - early_mean) / early_mean * 100)

    # ── Summary statistics ───────────────────────────────────────────────────
    summary_cols = ["total_system_load", "net_daily_intake",
                    "cbp_custody", "hhs_care", "hhs_discharged", "vol_7"]
    summary_stats = df[summary_cols].describe().round(2).to_dict()

    # ── Narrative bullets ────────────────────────────────────────────────────
    bullets = []

    # Bullet 1: peak
    bullets.append(
        f"📈 **Peak System Load:** {kpis['peak_system_load']:,} children on "
        f"{kpis['peak_load_date']} — the single highest recorded burden across the observation window."
    )

    # Bullet 2: current state
    slope_dir = "rising" if kpis["overall_load_trend_slope"] > 0 else "declining"
    bullets.append(
        f"📊 **Current State:** As of {kpis['latest_date']}, total children under care stands at "
        f"{kpis['current_total_under_care']:,} "
        f"({kpis['current_hhs_care']:,} in HHS + {kpis['current_cbp_custody']:,} in CBP). "
        f"The long-run trend is {slope_dir} at {abs(kpis['overall_load_trend_slope']):.2f} children/day."
    )

    # Bullet 3: discharge ratio
    ratio_pct = kpis["discharge_offset_ratio"] * 100
    efficiency_label = (
        "highly efficient" if ratio_pct >= 90
        else "moderately efficient" if ratio_pct >= 70
        else "under pressure"
    )
    bullets.append(
        f"🏥 **Discharge Efficiency:** The discharge offset ratio is {ratio_pct:.1f}%, "
        f"indicating the system is {efficiency_label} at processing exits relative to entries."
    )

    # Bullet 4: stress windows
    if stress_windows:
        longest = max(stress_windows, key=lambda w: w["days"])
        bullets.append(
            f"⚠️ **Sustained Stress Detected:** {len(stress_windows)} stress window(s) of ≥7 consecutive days "
            f"of positive net intake identified. The longest lasted {longest['days']} days "
            f"({longest['start'].strftime('%b %d')} – {longest['end'].strftime('%b %d, %Y')})."
        )
    else:
        bullets.append("✅ **No Prolonged Stress Windows:** No 7+ day continuous intake surges found.")

    # Bullet 5: relief
    if relief_periods:
        bullets.append(
            f"💧 **Relief Periods:** {len(relief_periods)} relief window(s) of declining net intake "
            f"observed — indicating temporary capacity recovery phases."
        )

    # Bullet 6: early vs late
    bullets.append(
        f"📉 **Trend Comparison:** System load is {trend_dir} — the latter half of the observation "
        f"period averaged {late_mean:,.0f} vs {early_mean:,.0f} in the earlier half "
        f"({trend_pct:.1f}% {'higher' if late_mean > early_mean else 'lower'})."
    )

    # Bullet 7: volatility
    vol_label = (
        "High" if kpis["care_load_volatility_pct"] > 30
        else "Moderate" if kpis["care_load_volatility_pct"] > 15
        else "Low"
    )
    bullets.append(
        f"📡 **Volatility:** {vol_label} system volatility at {kpis['care_load_volatility_pct']:.1f}% "
        f"of mean — {'indicating frequent surges' if vol_label == 'High' else 'indicating stable operations'}."
    )

    return {
        "high_load_periods": high_load,
        "stress_windows": stress_windows,
        "relief_periods": relief_periods,
        "early_vs_late": {
            "early_mean": round(early_mean, 1),
            "late_mean":  round(late_mean, 1),
            "direction":  trend_dir,
            "pct_change": round(trend_pct, 1),
        },
        "summary_stats": summary_stats,
        "narrative_bullets": bullets,
    }


# ═══════════════════════════════════════════════════════════════════════════
# STEP 9 — RESEARCH PAPER CONTENT
# ═══════════════════════════════════════════════════════════════════════════

def generate_research_paper(df: pd.DataFrame, kpis: dict, insights: dict) -> str:
    """
    Generate structured research paper content as a Markdown string.
    All figures are derived programmatically from the data.
    """
    evl = insights["early_vs_late"]
    n_stress = len(insights["stress_windows"])
    longest_stress = (
        max(insights["stress_windows"], key=lambda w: w["days"])
        if insights["stress_windows"] else None
    )
    peak_date   = kpis["peak_load_date"]
    peak_load   = kpis["peak_system_load"]
    trough_date = kpis["trough_load_date"]
    trough_load = kpis["trough_system_load"]
    ratio_pct   = round(kpis["discharge_offset_ratio"] * 100, 1)

    stress_desc = (
        f"The longest sustained stress window ran for {longest_stress['days']} days "
        f"({longest_stress['start'].strftime('%B %d')} – "
        f"{longest_stress['end'].strftime('%B %d, %Y')})."
        if longest_stress else "No prolonged stress windows were detected."
    )

    paper = f"""
# Monitoring Healthcare System Capacity in the U.S. Unaccompanied Children (UAC) Program
## A Data-Driven Analytics Study

---

## 1. Introduction

The United States Unaccompanied Children (UAC) program, administered by the Office of Refugee
Resettlement (ORR) within the Department of Health and Human Services (HHS), manages the care
and custody of children who enter the country without a parent or legal guardian. As a
humanitarian program operating at the intersection of immigration enforcement and child welfare,
it faces unique operational pressures driven by migration patterns, geopolitical events, and
seasonal trends.

This study presents a comprehensive data analytics pipeline designed to monitor, validate, and
visualize UAC program capacity across {kpis['total_days_observed']} days of observations
({kpis['date_range_start']} to {kpis['date_range_end']}). The goal is to transform raw
operational data into decision-grade intelligence for policy-makers, program administrators,
and humanitarian organizations.

---

## 2. Problem Statement

The UAC program must balance two competing imperatives: (1) ensuring the legal maximum custody
durations are not violated and children are transferred out of CBP detention rapidly, and
(2) maintaining sufficient HHS shelter capacity to absorb transferred children while pursuing
family reunification or long-term placement.

When intake surpasses discharge at a sustained rate, a **care backlog** accumulates. This study
quantifies that backlog, detects periods of operational stress, and provides leading indicators
for capacity planning.

Key research questions:
- When did system load peak, and what were the contributing dynamics?
- Does the discharge pipeline keep pace with incoming transfers?
- Are there detectable, recurring patterns of stress and relief?
- What early-warning signals can be automated for real-time monitoring?

---

## 3. Methodology

### 3.1 Data Source
The dataset was sourced from HHS public operational reporting, containing daily counts of:
- Children apprehended and placed in CBP custody
- Children in CBP custody (snapshot)
- Children transferred out of CBP to HHS
- Children in HHS care (snapshot)
- Children discharged from HHS care

### 3.2 Pipeline Architecture
The pipeline is structured across three modular Python components:
1. **data_processing.py** — Ingestion, cleaning, validation, feature engineering
2. **metrics.py** — KPI computation and insight generation
3. **dashboard.py** — Streamlit interactive visualization layer

### 3.3 Data Quality Controls
- Forward-fill imputation for missing daily observations with explicit row-level flagging
- Business rule validation: transfers ≤ CBP custody, discharges ≤ HHS care, no negatives
- Deduplication on date key
- Continuous daily date reindexing to expose gaps

### 3.4 Statistical Methods
- Linear regression for trend slope estimation
- 7/14-day centered moving averages for smoothing
- Rolling standard deviation as a volatility proxy
- Consecutive-run analysis for stress and relief window detection
- 90th percentile thresholding for high-load classification

---

## 4. Data Processing

The raw CSV contained {kpis['total_days_observed']} calendar days across the observation window.
After removing trailing empty rows and duplicates, a continuous daily index was constructed.
Forward-fill imputation was applied to bridge non-reporting days (weekends, federal holidays).

Derived features created:
| Feature | Formula |
|---|---|
| Total System Load | CBP Custody + HHS Care |
| Net Daily Intake | CBP Transfers − HHS Discharges |
| Care Load Growth Rate | Δ System Load (%) day-over-day |
| Backlog Indicator | Cumulative sum of positive net intakes |
| 7-day MA | Rolling 7-day average of System Load |
| 14-day MA | Rolling 14-day average of System Load |
| Volatility (7d) | Rolling 7-day standard deviation |

---

## 5. KPIs and Metrics

| KPI | Value |
|---|---|
| Peak System Load | {peak_load:,} children ({peak_date}) |
| Trough System Load | {trough_load:,} children ({trough_date}) |
| Latest Total Under Care | {kpis['current_total_under_care']:,} children |
| Discharge Offset Ratio | {ratio_pct}% |
| Care Load Volatility Index | {kpis['care_load_volatility_pct']}% |
| Avg Net Intake Pressure (30d) | {kpis['net_intake_pressure_30d']} children/day |
| Backlog Accumulation Rate | {kpis['backlog_accumulation_rate']} children/day |
| Overall Trend (slope) | {kpis['overall_load_trend_slope']} children/day |

The **Discharge Offset Ratio** of {ratio_pct}% indicates that for every child transferred into
HHS care, approximately {ratio_pct/100:.2f} are discharged — {'suggesting near-equilibrium' if ratio_pct >= 90 else 'indicating net backlog accumulation'}.

---

## 6. Key Insights

### 6.1 System Load Trajectory
System load reached its maximum of {peak_load:,} children on {peak_date}. The overall trend
direction is **{evl['direction']}**, with the latter half of the observation period averaging
{evl['late_mean']:,.0f} vs {evl['early_mean']:,.0f} children in the earlier half
({evl['pct_change']}% {'increase' if evl['direction'] == 'increasing' else 'decrease'}).

### 6.2 Sustained Stress Windows
Analysis identified {n_stress} sustained stress window(s) of ≥7 consecutive days of positive
net intake. {stress_desc}

### 6.3 Relief Periods
{len(insights['relief_periods'])} relief period(s) were detected — windows where discharges
exceeded new arrivals, temporarily reducing system backlog.

### 6.4 Volatility Assessment
The care load volatility index of {kpis['care_load_volatility_pct']}% reflects the degree
of unpredictability in daily census figures. {'High volatility' if kpis['care_load_volatility_pct'] > 30 else 'Moderate volatility'} complicates staff scheduling and shelter
procurement planning.

---

## 7. Policy Recommendations

Based on the analytical findings, the following evidence-based recommendations are proposed:

1. **Surge Capacity Planning:** Given the documented peak of {peak_load:,} and volatility
   of {kpis['care_load_volatility_pct']}%, HHS should maintain a minimum 20% buffer above
   current census as standby shelter capacity.

2. **Discharge Pipeline Optimization:** A discharge offset ratio of {ratio_pct}% suggests
   {'near-parity but' if ratio_pct >= 90 else ''} room for improvement in sponsor matching
   and reunification processing. Reducing average length-of-stay by even 5% could meaningfully
   reduce peak load.

3. **Early Warning Triggers:** Automated alerts should fire when:
   - 7-day MA exceeds its own 30-day MA by >5%
   - Net daily intake is positive for ≥5 consecutive days
   - Volatility index exceeds 20% in any rolling 7-day window

4. **Seasonal Staffing:** The identification of {n_stress} stress windows suggests predictable
   surge seasons. Proactive staff augmentation during these windows would reduce burnout and
   maintain care quality standards.

5. **Data Reporting Continuity:** The presence of weekend/holiday data gaps requires forward-fill
   imputation. Real-time reporting should be mandated seven days per week to enable more
   accurate operational monitoring.

---

## 8. Conclusion

This study demonstrates the feasibility of a fully automated analytics pipeline for monitoring
UAC program healthcare capacity. By applying rigorous data validation, feature engineering, and
statistical analysis, the pipeline surfaces actionable insights that would be invisible in raw
tabular data alone.

The {evl['direction']} trend in system load, combined with a discharge offset ratio of {ratio_pct}%
and {n_stress} detected stress windows, underscores the need for dynamic, data-informed capacity
management. The accompanying Streamlit dashboard operationalizes these findings into a real-time
monitoring tool suitable for program administrators at all levels.

---

*Generated automatically by the UAC Analytics Pipeline | Data through {kpis['date_range_end']}*
"""
    return paper.strip()


# ═══════════════════════════════════════════════════════════════════════════
# STEP 10 — EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

def generate_executive_summary(kpis: dict, insights: dict) -> str:
    """
    Generate a concise executive summary with key risks and recommendations.
    """
    evl    = insights["early_vs_late"]
    n_str  = len(insights["stress_windows"])
    ratio  = round(kpis["discharge_offset_ratio"] * 100, 1)
    slope  = kpis["overall_load_trend_slope"]
    slope_dir = "rising" if slope > 0 else "declining"
    vol    = kpis["care_load_volatility_pct"]

    risk_level = (
        "🔴 HIGH"   if vol > 30 or ratio < 70 or n_str > 5
        else "🟡 MODERATE" if vol > 15 or ratio < 85 or n_str > 2
        else "🟢 LOW"
    )

    summary = f"""
## Executive Summary — UAC Program Capacity Monitor

**Data Period:** {kpis['date_range_start']} → {kpis['date_range_end']}
**Overall Risk Level:** {risk_level}

---

### Situation Overview
As of **{kpis['latest_date']}**, the UAC program is caring for **{kpis['current_total_under_care']:,}
children** total — {kpis['current_hhs_care']:,} in HHS facilities and {kpis['current_cbp_custody']:,}
in CBP custody. The system load trend is **{slope_dir}** (slope: {abs(slope):.2f} children/day).
System load peaked at **{kpis['peak_system_load']:,} on {kpis['peak_load_date']}**.

---

### Key Risks

| Risk | Metric | Status |
|---|---|---|
| Intake Surge | Net Intake (30d avg): {kpis['net_intake_pressure_30d']:.1f}/day | {'⚠️ Elevated' if kpis['net_intake_pressure_30d'] > 5 else '✅ Stable'} |
| Discharge Gap | Offset Ratio: {ratio}% | {'⚠️ Below 90%' if ratio < 90 else '✅ Healthy'} |
| Volatility | Index: {vol:.1f}% | {'🔴 High' if vol > 30 else '🟡 Moderate' if vol > 15 else '✅ Low'} |
| Stress Events | {n_str} stress windows detected | {'⚠️ Multiple' if n_str > 2 else '✅ Minimal'} |
| Backlog | Rate: {kpis['backlog_accumulation_rate']:.1f}/day | {'⚠️ Growing' if kpis['backlog_accumulation_rate'] > 10 else '✅ Controlled'} |

---

### System Stress Periods
{'- ' + chr(10).join([f"{w['start'].strftime('%b %d')} – {w['end'].strftime('%b %d, %Y')}: {w['days']} consecutive days of positive intake (avg {w['avg_net_intake']:.1f}/day)" for w in insights['stress_windows']]) if insights['stress_windows'] else 'No major sustained stress periods detected.'}

---

### Actionable Recommendations

1. **Maintain 20% Surge Capacity Buffer** above current census ({kpis['current_total_under_care']:,})
   — targeted buffer: ~{int(kpis['current_total_under_care'] * 1.2):,} beds.
2. **Accelerate Sponsor Matching** to improve discharge offset ratio above 90%
   (currently {ratio}%).
3. **Activate Early Warning Alerts** when 7-day MA rises >5% above its 30-day baseline.
4. **Seasonal Staffing Plans:** Pre-position staff and contract shelters ahead of identified
   surge windows.
5. **Daily Reporting Mandate:** Eliminate data gaps by requiring 7-day reporting to reduce
   imputation and improve lead-time on trend detection.

---
*Programmatically generated — UAC Analytics Pipeline v1.0*
"""
    return summary.strip()


if __name__ == "__main__":
    from data_processing import run_pipeline
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "HHS_Unaccompanied_Alien_Children_Program__1_.csv"
    df, _, meta, val_report = run_pipeline(path)

    kpis    = compute_kpis(df)
    insights = generate_insights(df, kpis)

    print("=== KPIs ===")
    for k, v in kpis.items():
        print(f"  {k}: {v}")

    print("\n=== Narrative Insights ===")
    for b in insights["narrative_bullets"]:
        print(" ", b)

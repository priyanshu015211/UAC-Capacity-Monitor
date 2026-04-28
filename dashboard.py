"""
dashboard.py
============
UAC Healthcare System Capacity Analytics — Streamlit Dashboard

Run with:
    streamlit run dashboard.py -- --data /path/to/file.csv

Version: 1.2.0
"""

import re
import argparse
from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from data_processing import run_pipeline, resample_data
from metrics import compute_kpis, generate_insights, generate_executive_summary


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UAC Capacity Monitor",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<style>
html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-size: 15px;
    -webkit-font-smoothing: antialiased;
    line-height: 1.6;
    color: #1a202c;
    background-color: #ffffff;
}
.block-container {
    padding-top: 2.5rem;
    padding-bottom: 3rem;
    max-width: 1400px;
    background-color: #ffffff;
}

/* Page header */
.page-title {
    font-size: 2.05rem;
    font-weight: 700;
    color: #1a202c;
    letter-spacing: -0.015em;
    line-height: 1.2;
    margin: 0 0 0.4rem 0;
}
.page-subtitle {
    font-size: 0.925rem;
    font-weight: 400;
    color: #64748b;
    line-height: 1.6;
    margin: 0 0 2rem 0;
}

/* Section headings */
.section-heading {
    font-size: 0.73rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94a3b8;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 0.5rem;
    margin-top: 0;
    margin-bottom: 1.25rem;
}

/* KPI cards */
.kpi-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1.1rem 1.25rem;
    text-align: left;
}
.kpi-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 0.35rem;
    line-height: 1.4;
}
.kpi-value {
    font-size: 1.95rem;
    font-weight: 700;
    color: #1a202c;
    line-height: 1.1;
    letter-spacing: -0.025em;
}
.kpi-note {
    font-size: 0.72rem;
    font-weight: 400;
    color: #94a3b8;
    margin-top: 0.3rem;
    line-height: 1.5;
}
.kpi-note.warn  { color: #d97706; }
.kpi-note.good  { color: #16a34a; }
.kpi-note.alert { color: #dc2626; }

/* Insight cards */
.insight-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #2563eb;
    border-radius: 6px;
    padding: 0.875rem 1.1rem;
    margin-bottom: 0.625rem;
    font-size: 0.9rem;
    font-weight: 400;
    line-height: 1.6;
    color: #374151;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #f8fafc;
    border-right: 1px solid #e2e8f0;
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Widget labels */
label,
.stSelectbox label,
.stMultiSelect label,
.stDateInput label,
.stCheckbox label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #94a3b8 !important;
    line-height: 1.5 !important;
}

/* Tab labels */
button[data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}

/* Streamlit overrides */
.stApp { background-color: #ffffff; }
.stMarkdown, .stText, p, li, span { color: #1a202c; }
.stDataFrame { background-color: #ffffff; }
div[data-testid="stDecoration"] { display: none; }

/* Footer */
.page-footer {
    font-size: 0.75rem;
    font-weight: 400;
    color: #94a3b8;
    text-align: center;
    padding-top: 1.5rem;
    margin-top: 3rem;
    border-top: 1px solid #e2e8f0;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# CHART DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
CHART_BASE = dict(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font=dict(color="#64748b", family="Inter, system-ui, sans-serif", size=13),
    xaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", showgrid=True, tickfont=dict(size=12)),
    yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", showgrid=True, tickfont=dict(size=12)),
    legend=dict(bgcolor="rgba(255,255,255,0)", bordercolor="#e2e8f0", borderwidth=1, font=dict(size=12)),
    margin=dict(l=48, r=24, t=56, b=44),
    hoverlabel=dict(bgcolor="#1e293b", font_color="#f8fafc", bordercolor="#334155", font_size=12),
    title_font=dict(size=15, color="#1e293b", family="Inter, sans-serif"),
    title_x=0,
    title_pad=dict(b=14),
)

C = {
    "blue":   "#2563eb",
    "purple": "#7c3aed",
    "orange": "#d97706",
    "red":    "#dc2626",
    "sky":    "#0284c7",
    "green":  "#16a34a",
    "pink":   "#db2777",
    "slate":  "#475569",
}


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading data...")
def load_data(filepath: str):
    df, df_anomaly, meta, val_report = run_pipeline(filepath)
    kpis     = compute_kpis(df)
    insights = generate_insights(df, kpis)
    return df, df_anomaly, meta, val_report, kpis, insights


# ─────────────────────────────────────────────────────────────────────────────
# CHART BUILDERS — titles written as findings, peak annotated on every chart
# ─────────────────────────────────────────────────────────────────────────────

def _add_peak_annotation(fig, peak_date, peak_val, label="Peak"):
    """Add a vertical reference line + callout at the peak date."""
    fig.add_vline(
        x=peak_date,
        line_color="#dc2626",
        line_width=1,
        line_dash="dot",
        opacity=0.6,
    )
    fig.add_annotation(
        x=peak_date,
        y=peak_val,
        text=f"{label}: {peak_val:,.0f}",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#dc2626",
        arrowsize=0.8,
        ax=40,
        ay=-36,
        font=dict(size=11, color="#dc2626", family="Inter, sans-serif"),
        bgcolor="#ffffff",
        bordercolor="#dc2626",
        borderwidth=1,
        borderpad=4,
    )
    return fig


def chart_system_load(df: pd.DataFrame, kpis: dict) -> go.Figure:
    peak_val  = kpis["peak_system_load"]
    peak_date = pd.Timestamp(kpis["peak_load_date"])
    latest    = kpis["current_total_under_care"]
    pct_down  = round((peak_val - latest) / peak_val * 100)
    slope_dir = "falling" if kpis["overall_load_trend_slope"] < 0 else "rising"

    title = (
        f"Peaked at {peak_val:,} children in {peak_date.strftime('%B %Y')} — "
        f"down {pct_down}% since, currently {slope_dir}"
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["total_system_load"],
        mode="lines", name="Total load",
        line=dict(color=C["blue"], width=1.5),
        fill="tozeroy", fillcolor="rgba(37,99,235,0.05)",
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["ma_7"],
        mode="lines", name="7-day average",
        line=dict(color=C["purple"], width=2, dash="dot"),
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["ma_14"],
        mode="lines", name="14-day average",
        line=dict(color=C["pink"], width=2, dash="dash"),
    ))
    # 60-day linear projection
    x_num = np.arange(len(df))
    coeffs = np.polyfit(x_num, df["total_system_load"].ffill(), 1)
    last_date = df["date"].iloc[-1]
    proj_dates = pd.date_range(start=last_date, periods=61, freq="D")[1:]
    proj_vals  = coeffs[0] * np.arange(len(df), len(df) + 60) + coeffs[1]
    proj_vals  = np.clip(proj_vals, 0, None)
    fig.add_trace(go.Scatter(
        x=proj_dates, y=proj_vals,
        mode="lines", name="60-day projection",
        line=dict(color=C["orange"], width=2, dash="dot"),
        opacity=0.7,
    ))
    fig.add_annotation(
        x=proj_dates[-1], y=proj_vals[-1],
        text=f"Projected: {int(proj_vals[-1]):,}",
        showarrow=False,
        font=dict(size=11, color=C["orange"], family="Inter, sans-serif"),
        xanchor="left", xshift=6,
    )

    fig.update_layout(
        **CHART_BASE,
        title=title,
        xaxis_title="Date",
        yaxis_title="Children",
        hovermode="x unified",
    )
    _add_peak_annotation(fig, peak_date, peak_val)
    return fig


def chart_cbp_vs_hhs(df: pd.DataFrame, kpis: dict) -> go.Figure:
    avg_cbp = kpis["avg_cbp_custody"]
    avg_hhs = kpis["avg_hhs_care"]
    pct_hhs = round(avg_hhs / (avg_cbp + avg_hhs) * 100)
    title = (
        f"HHS facilities hold {pct_hhs}% of the average load — "
        f"CBP custody averages {avg_cbp:,.0f}, HHS averages {avg_hhs:,.0f}"
    )

    # Find peak of HHS care for annotation
    peak_hhs_idx = df["hhs_care"].idxmax()
    peak_hhs_date = df.loc[peak_hhs_idx, "date"]
    peak_hhs_val  = df.loc[peak_hhs_idx, "hhs_care"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["cbp_custody"],
        mode="lines", name="CBP custody",
        line=dict(color=C["sky"], width=2),
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["hhs_care"],
        mode="lines", name="HHS care",
        line=dict(color=C["green"], width=2),
    ))
    fig.update_layout(
        **CHART_BASE,
        title=title,
        xaxis_title="Date",
        yaxis_title="Children",
        hovermode="x unified",
    )
    _add_peak_annotation(fig, peak_hhs_date, peak_hhs_val, "HHS peak")
    return fig


def chart_net_intake(df: pd.DataFrame, kpis: dict) -> go.Figure:
    net_30d = kpis["net_intake_pressure_30d"]
    direction = "running above zero" if net_30d > 0 else "running below zero"
    title = (
        f"Transfers minus discharges — 30-day average is {net_30d:+.1f}/day, "
        f"{direction}"
    )
    colors = [C["red"] if v >= 0 else C["green"] for v in df["net_daily_intake"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["date"], y=df["net_daily_intake"],
        marker_color=colors,
        name="Net intake",
        hovertemplate="%{x|%b %d, %Y}<br>Net: %{y:+,.0f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color="#cbd5e1", line_width=1, opacity=0.8)
    fig.update_layout(
        **CHART_BASE,
        title=title,
        xaxis_title="Date",
        yaxis_title="Children",
    )
    return fig


def chart_backlog(df: pd.DataFrame, kpis: dict) -> go.Figure:
    backlog_rate = kpis["backlog_accumulation_rate"]
    final_backlog = df["backlog_indicator"].iloc[-1]
    title = (
        f"Cumulative backlog reached {final_backlog:,.0f} — "
        f"building at {backlog_rate:.1f} children/day on average when intake is positive"
    )
    peak_b_idx  = df["backlog_indicator"].idxmax()
    peak_b_date = df.loc[peak_b_idx, "date"]
    peak_b_val  = df.loc[peak_b_idx, "backlog_indicator"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["backlog_indicator"],
        mode="lines", name="Cumulative backlog",
        line=dict(color=C["orange"], width=2),
        fill="tozeroy", fillcolor="rgba(217,119,6,0.06)",
    ))
    fig.update_layout(
        **CHART_BASE,
        title=title,
        xaxis_title="Date",
        yaxis_title="Children (cumulative)",
    )
    _add_peak_annotation(fig, peak_b_date, peak_b_val, "Backlog peak")
    return fig


def chart_discharge_ratio(df: pd.DataFrame, kpis: dict) -> go.Figure:
    ratio = round(kpis["discharge_offset_ratio"] * 100, 1)
    status = "near equilibrium" if ratio >= 90 else "below the 90% equilibrium target"
    title = (
        f"Discharge ratio is {ratio}% overall — system is {status}. "
        f"Above 100% means discharges are outpacing new transfers."
    )
    df = df.copy()
    df["discharge_ratio_30d"] = (
        df["hhs_discharged"].rolling(30, min_periods=7).sum()
        / df["cbp_transfers"].rolling(30, min_periods=7).sum().replace(0, np.nan)
        * 100
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["discharge_ratio_30d"],
        mode="lines", name="30-day discharge ratio",
        line=dict(color=C["purple"], width=2),
        fill="tozeroy", fillcolor="rgba(124,58,237,0.05)",
    ))
    fig.add_hline(
        y=100, line_color=C["green"], line_width=1, line_dash="dash",
        annotation_text="Equilibrium (100%)",
        annotation_font_color=C["green"],
    )
    fig.update_layout(
        **CHART_BASE,
        title=title,
        xaxis_title="Date",
        yaxis_title="Ratio (%)",
    )
    return fig


def chart_volatility(df: pd.DataFrame, kpis: dict) -> go.Figure:
    vol = kpis["care_load_volatility_pct"]
    vol_label = "high" if vol > 30 else ("moderate" if vol > 15 else "low")
    title = (
        f"Volatility is {vol_label} at {vol:.1f}% of the mean — "
        f"spikes make short-term planning difficult"
    )
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["total_system_load"],
        mode="lines", name="System load",
        line=dict(color=C["blue"], width=1.5, dash="dot"),
        opacity=0.35,
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["vol_7"],
        mode="lines", name="7-day volatility",
        line=dict(color=C["orange"], width=2),
        fill="tozeroy", fillcolor="rgba(217,119,6,0.06)",
    ), secondary_y=True)
    fig.update_layout(**CHART_BASE, title=title, hovermode="x unified")
    axis_style = dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", tickfont=dict(size=12))
    fig.update_yaxes(title_text="System load", secondary_y=False, **axis_style)
    fig.update_yaxes(title_text="Std. deviation", secondary_y=True, **axis_style)
    return fig


def chart_monthly_heatmap(df: pd.DataFrame) -> go.Figure:
    df_m = df.copy()
    df_m["year_str"]  = df_m["date"].dt.year.astype(str)
    df_m["month_str"] = df_m["date"].dt.strftime("%b")
    pivot = df_m.pivot_table(
        values="total_system_load", index="year_str", columns="month_str", aggfunc="mean"
    )
    month_order = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    pivot = pivot.reindex(columns=[m for m in month_order if m in pivot.columns])
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="Blues",
        text=np.round(pivot.values, 0),
        texttemplate="%{text:.0f}",
        hovertemplate="Year: %{y}<br>Month: %{x}<br>Avg load: %{z:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        **CHART_BASE,
        title="Average monthly load — darker means more children in care",
        xaxis_title="Month",
        yaxis_title="Year",
    )
    return fig


def chart_stacked_area(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["cbp_custody"],
        mode="lines", name="CBP custody",
        line=dict(color=C["sky"], width=0),
        stackgroup="one", fillcolor="rgba(2,132,199,0.3)",
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["hhs_care"],
        mode="lines", name="HHS care",
        line=dict(color=C["green"], width=0),
        stackgroup="one", fillcolor="rgba(22,163,74,0.3)",
    ))
    fig.update_layout(
        **CHART_BASE,
        title="Combined load — CBP and HHS stacked",
        xaxis_title="Date",
        yaxis_title="Children",
        hovermode="x unified",
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def kpi_card(label: str, value: str, note: str = "", note_type: str = ""):
    note_html = f'<div class="kpi-note {note_type}">{note}</div>' if note else ""
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{note_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def section(title: str):
    st.markdown(
        f'<div class="section-heading">{title}</div>',
        unsafe_allow_html=True,
    )


def spacer(size: str = "1rem"):
    st.markdown(f'<div style="height:{size}"></div>', unsafe_allow_html=True)


def strip_emoji(text: str) -> str:
    return re.sub(r'[^\x00-\x7F]+', '', text).strip()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Locate data file
    data_path = None
    try:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--data", default=None)
        args, _ = parser.parse_known_args()
        if args.data:
            data_path = args.data
    except Exception:
        pass

    if data_path is None:
        for candidate in [
            "HHS_Unaccompanied_Alien_Children_Program__1_.csv",
            "data/HHS_Unaccompanied_Alien_Children_Program__1_.csv",
            "/mnt/user-data/uploads/HHS_Unaccompanied_Alien_Children_Program__1_.csv",
        ]:
            if Path(candidate).exists():
                data_path = candidate
                break

    # Page header
    st.markdown(
        '<div class="page-title">UAC Program — Capacity Monitor</div>'
        '<div class="page-subtitle">'
        'Unaccompanied Children Program &nbsp;&middot;&nbsp; '
        'HHS / Office of Refugee Resettlement'
        '</div>',
        unsafe_allow_html=True,
    )

    if data_path is None or not Path(data_path).exists():
        st.error(
            "No data file found. Upload a CSV below, or pass "
            "--data /path/to/file.csv when launching."
        )
        uploaded = st.file_uploader("Upload CSV", type="csv")
        if uploaded:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded.read())
                data_path = tmp.name
        else:
            st.stop()

    df, df_anomaly, meta, val_report, kpis, insights = load_data(data_path)

    # ── Sidebar — only the controls that matter ───────────────────────────────
    with st.sidebar:
        section("Filters")

        min_date = df["date"].min().date()
        max_date = df["date"].max().date()
        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        spacer("0.75rem")

        granularity_label = st.selectbox(
            "Time granularity",
            ["Daily", "Weekly", "Monthly"],
        )
        _pd_ver  = tuple(int(x) for x in pd.__version__.split(".")[:2])
        _monthly = "ME" if _pd_ver >= (2, 2) else "M"
        gran_map = {"Daily": "D", "Weekly": "W", "Monthly": _monthly}
        granularity = gran_map[granularity_label]

        spacer("0.75rem")

        metric_options = {
            "Total system load": "total_system_load",
            "CBP custody":       "cbp_custody",
            "HHS care":          "hhs_care",
            "Net daily intake":  "net_daily_intake",
            "Backlog indicator": "backlog_indicator",
            "7-day volatility":  "vol_7",
        }
        selected_metrics = st.multiselect(
            "Metrics to compare",
            list(metric_options.keys()),
            default=["Total system load", "Net daily intake"],
        )

    # ── Apply filters ─────────────────────────────────────────────────────────
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_dt = pd.Timestamp(date_range[0])
        end_dt   = pd.Timestamp(date_range[1])
    else:
        start_dt = pd.Timestamp(min_date)
        end_dt   = pd.Timestamp(max_date)

    df_filtered  = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)].copy()
    df_resampled = resample_data(df_filtered, granularity)
    kpis_f       = compute_kpis(df_filtered)
    insights_f   = generate_insights(df_filtered, kpis_f)

    # ── 6 KPI cards — the numbers that actually matter ────────────────────────
    section("At a glance")
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        kpi_card("Children in care", f"{kpis_f['current_total_under_care']:,}",
                 f"As of {kpis_f['latest_date']}")
    with c2:
        kpi_card("In HHS facilities", f"{kpis_f['current_hhs_care']:,}")
    with c3:
        kpi_card("In CBP custody", f"{kpis_f['current_cbp_custody']:,}")
    with c4:
        ratio = round(kpis_f["discharge_offset_ratio"] * 100, 1)
        nt    = "good" if ratio >= 90 else "warn"
        ns    = "On target" if ratio >= 90 else "Below 90% target"
        kpi_card("Discharge ratio", f"{ratio}%", ns, nt)
    with c5:
        slope = kpis_f["overall_load_trend_slope"]
        nt    = "alert" if slope > 0 else "good"
        ns    = "Rising" if slope > 0 else "Declining"
        kpi_card("Daily trend", f"{slope:+.2f}/day", ns, nt)
    with c6:
        n_str = len(insights_f["stress_windows"])
        nt    = "alert" if n_str > 4 else ("warn" if n_str > 1 else "good")
        ns    = "Periods of 7+ consecutive days of rising intake"
        kpi_card("Stress windows", str(n_str), ns, nt)

    spacer("1rem")

    # ── Secondary KPI row — methodology-required metrics ─────────────────────
    section("System health indicators")
    s1, s2, s3, s4 = st.columns(4)

    with s1:
        vol = kpis_f["care_load_volatility_pct"]
        vol_label = "High" if vol > 30 else ("Moderate" if vol > 15 else "Low")
        vol_nt = "alert" if vol > 30 else ("warn" if vol > 15 else "good")
        kpi_card("Volatility index", f"{vol:.1f}%",
                 f"{vol_label} — variation relative to mean load", vol_nt)
    with s2:
        br = kpis_f["backlog_accumulation_rate"]
        kpi_card("Backlog accumulation rate", f"{br:.1f}/day",
                 "Average intake on days when transfers exceed discharges", "warn")
    with s3:
        ni = kpis_f["net_intake_pressure_30d"]
        ni_nt = "alert" if ni > 0 else "good"
        ni_ns = "Intake exceeds discharges" if ni > 0 else "Discharges exceed intake"
        kpi_card("Net intake pressure (30d)", f"{ni:+.1f}/day", ni_ns, ni_nt)
    with s4:
        kpi_card("Peak load recorded", f"{kpis_f['peak_system_load']:,}",
                 kpis_f['peak_load_date'])

    spacer("2rem")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "System overview",
        "CBP vs. HHS",
        "Intake and backlog",
        "Metric comparison",
        "Findings",
        "Data quality",
    ])

    # ── Tab 1: System overview ────────────────────────────────────────────────
    with tab1:
        spacer("0.5rem")
        section("System load")
        st.plotly_chart(
            chart_system_load(df_resampled, kpis_f),
            use_container_width=True,
        )

        spacer("1rem")
        col_l, col_r = st.columns(2)
        with col_l:
            section("Volatility")
            st.plotly_chart(
                chart_volatility(df_resampled, kpis_f),
                use_container_width=True,
            )
        with col_r:
            section("Seasonal pattern")
            st.plotly_chart(
                chart_monthly_heatmap(df_filtered),
                use_container_width=True,
            )

    # ── Tab 2: CBP vs HHS ─────────────────────────────────────────────────────
    with tab2:
        spacer("0.5rem")
        section("Daily census")
        st.plotly_chart(
            chart_cbp_vs_hhs(df_resampled, kpis_f),
            use_container_width=True,
        )

        spacer("1rem")
        col_l, col_r = st.columns(2)
        with col_l:
            section("Discharge ratio")
            st.plotly_chart(
                chart_discharge_ratio(df_resampled, kpis_f),
                use_container_width=True,
            )
        with col_r:
            section("Combined load")
            st.plotly_chart(
                chart_stacked_area(df_resampled),
                use_container_width=True,
            )

    # ── Tab 3: Intake and backlog ─────────────────────────────────────────────
    with tab3:
        spacer("0.5rem")
        section("Daily intake pressure")
        st.plotly_chart(
            chart_net_intake(df_resampled, kpis_f),
            use_container_width=True,
        )

        spacer("1rem")
        section("Backlog accumulation")
        st.plotly_chart(
            chart_backlog(df_resampled, kpis_f),
            use_container_width=True,
        )

    # ── Tab 4: Metric comparison ──────────────────────────────────────────────
    with tab4:
        spacer("0.5rem")
        section("Metric comparison")
        if selected_metrics:
            palette = [C["blue"], C["purple"], C["orange"], C["sky"], C["green"], C["pink"]]
            fig_cmp = go.Figure()
            for i, m_label in enumerate(selected_metrics):
                col_key = metric_options[m_label]
                if col_key in df_resampled.columns:
                    fig_cmp.add_trace(go.Scatter(
                        x=df_resampled["date"],
                        y=df_resampled[col_key],
                        mode="lines",
                        name=m_label,
                        line=dict(color=palette[i % len(palette)], width=2),
                    ))
            fig_cmp.update_layout(
                **CHART_BASE,
                title="Selected metrics overlaid — use the sidebar to add or remove metrics",
                hovermode="x unified",
            )
            fig_cmp.update_layout(legend=dict(
                orientation="h",
                yanchor="top", y=-0.15,
                xanchor="center", x=0.5,
            ))
            st.plotly_chart(fig_cmp, use_container_width=True)

            spacer("1rem")
            section("Summary statistics for selected metrics")
            stat_rows = []
            for m_label in selected_metrics:
                col_key = metric_options[m_label]
                if col_key in df_resampled.columns:
                    s = df_resampled[col_key].dropna()
                    stat_rows.append({
                        "Metric":   m_label,
                        "Min":      f"{s.min():,.1f}",
                        "Max":      f"{s.max():,.1f}",
                        "Mean":     f"{s.mean():,.1f}",
                        "Std dev":  f"{s.std():,.1f}",
                        "Latest":   f"{s.iloc[-1]:,.1f}" if len(s) else "—",
                    })
            if stat_rows:
                st.dataframe(pd.DataFrame(stat_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Select one or more metrics from the sidebar to compare them here.")

    # ── Tab 5: Findings ───────────────────────────────────────────────────────
    with tab5:
        spacer("0.5rem")
        section("What the data shows")

        for bullet in insights_f["narrative_bullets"]:
            clean = re.sub(r"\*\*(.*?)\*\*", r"\1", bullet)
            clean = strip_emoji(clean)
            st.markdown(
                f'<div class="insight-card">{clean}</div>',
                unsafe_allow_html=True,
            )

        spacer("1.5rem")
        section("Early vs late period comparison")
        mid_date = df_filtered["date"].min() + (df_filtered["date"].max() - df_filtered["date"].min()) / 2
        df_early = df_filtered[df_filtered["date"] <= mid_date]
        df_late  = df_filtered[df_filtered["date"] >  mid_date]
        if len(df_early) > 0 and len(df_late) > 0:
            def _period_stats(d):
                return {
                    "Avg children in care":    f"{d['total_system_load'].mean():,.0f}",
                    "Avg HHS care":            f"{d['hhs_care'].mean():,.0f}",
                    "Avg CBP custody":         f"{d['cbp_custody'].mean():,.0f}",
                    "Avg daily net intake":    f"{d['net_daily_intake'].mean():+.1f}",
                    "Discharge ratio":         f"{(d['hhs_discharged'].sum()/d['cbp_transfers'].sum()*100) if d['cbp_transfers'].sum()>0 else 0:.1f}%",
                    "Peak load":               f"{d['total_system_load'].max():,.0f}",
                }
            stats_e = _period_stats(df_early)
            stats_l = _period_stats(df_late)
            cmp_df = pd.DataFrame({
                "Metric": list(stats_e.keys()),
                f"Early ({df_early['date'].min().strftime('%b %Y')} \u2013 {df_early['date'].max().strftime('%b %Y')})": list(stats_e.values()),
                f"Late  ({df_late['date'].min().strftime('%b %Y')} \u2013 {df_late['date'].max().strftime('%b %Y')})":   list(stats_l.values()),
            })
            st.dataframe(cmp_df, use_container_width=True, hide_index=True)

        spacer("1.5rem")
        col_l, col_r = st.columns(2)

        with col_l:
            section("Stress windows — 7 or more consecutive days of positive intake")
            if insights_f["stress_windows"]:
                stress_df = pd.DataFrame(insights_f["stress_windows"])
                stress_df["start"] = stress_df["start"].dt.strftime("%b %d, %Y")
                stress_df["end"]   = stress_df["end"].dt.strftime("%b %d, %Y")
                stress_df["avg_net_intake"] = stress_df["avg_net_intake"].round(1)
                stress_df.columns = ["Start", "End", "Days", "Avg net intake"]
                st.dataframe(stress_df, use_container_width=True, hide_index=True)
            else:
                st.info("No stress windows found in the selected date range.")

        with col_r:
            section("Relief periods — 3 or more consecutive days of declining intake")
            if insights_f["relief_periods"]:
                relief_df = pd.DataFrame(insights_f["relief_periods"])
                relief_df["start"] = relief_df["start"].dt.strftime("%b %d, %Y")
                relief_df["end"]   = relief_df["end"].dt.strftime("%b %d, %Y")
                relief_df["avg_relief"] = relief_df["avg_relief"].round(1)
                relief_df.columns = ["Start", "End", "Days", "Avg daily relief"]
                st.dataframe(relief_df, use_container_width=True, hide_index=True)
            else:
                st.info("No relief periods found in the selected date range.")

        spacer("1.5rem")
        section("Executive summary")
        exec_md    = generate_executive_summary(kpis_f, insights_f)
        exec_clean = strip_emoji(exec_md)
        st.markdown(exec_clean)

        spacer("1rem")
        from metrics import generate_research_paper
        research_paper = generate_research_paper(df_filtered, kpis_f, insights_f)
        st.download_button(
            "Download full report (Markdown)",
            data=research_paper,
            file_name="UAC_Capacity_Report.md",
            mime="text/markdown",
        )

    # ── Tab 6: Data quality ───────────────────────────────────────────────────
    with tab6:
        spacer("0.5rem")
        section("Data quality summary")

        vr1, vr2, vr3, vr4 = st.columns(4)
        with vr1:
            kpi_card("Total records", f"{val_report['total_records']:,}",
                     f"{meta['n_raw_rows']:,} raw rows processed")
        with vr2:
            pct = val_report["anomaly_pct"]
            nt  = "alert" if pct > 10 else ("warn" if pct > 5 else "good")
            kpi_card("Flagged records", f"{val_report['anomaly_count']:,}",
                     f"{pct}% of all records", nt)
        with vr3:
            kpi_card("Estimated values", f"{meta['n_imputed_rows']:,}",
                     "Filled by forward-fill on non-reporting days")
        with vr4:
            kpi_card("Duplicates removed", f"{meta['n_duplicates_removed']:,}")

        spacer("1.5rem")
        col_l, col_r = st.columns(2)

        with col_l:
            section("Validation rule checks")
            rules_df = pd.DataFrame([
                {"Rule": "Transfers exceed CBP custody count",
                 "Violations": val_report["rule_transfer_exceeds_custody"]},
                {"Rule": "Discharges exceed HHS care count",
                 "Violations": val_report["rule_discharge_exceeds_care"]},
                {"Rule": "Negative value in any column",
                 "Violations": val_report["rule_negative_values"]},
            ])
            st.dataframe(rules_df, use_container_width=True, hide_index=True)

        with col_r:
            section("Sample of flagged records")
            if len(df_anomaly) > 0:
                display_cols = ["date", "cbp_custody", "cbp_transfers",
                                "hhs_care", "hhs_discharged", "anomaly_flags"]
                anom_display = df_anomaly[display_cols].head(20).copy()
                anom_display["date"] = anom_display["date"].dt.strftime("%Y-%m-%d")
                st.dataframe(anom_display, use_container_width=True, hide_index=True)
            else:
                st.success("No anomalies detected.")

        spacer("1.5rem")
        section("Days estimated by forward-fill")
        imputed_rows = df_filtered[df_filtered["is_imputed"]].copy()
        if len(imputed_rows) > 0:
            imputed_rows["week"]     = imputed_rows["date"].dt.isocalendar().week.astype(int)
            imputed_rows["year_str"] = imputed_rows["date"].dt.year.astype(str)
            fig_imp = px.scatter(
                imputed_rows,
                x="week", y="year_str",
                color_discrete_sequence=[C["orange"]],
                title="Each dot is a week with at least one estimated value — typically weekends and federal holidays",
                labels={"week": "ISO week number", "year_str": "Year"},
            )
            fig_imp.update_traces(marker=dict(size=10, symbol="square"))
            fig_imp.update_layout(**CHART_BASE)
            st.plotly_chart(fig_imp, use_container_width=True)
        else:
            st.success("No estimated values in the selected date range.")

        spacer("1rem")
        with st.expander("View processed data table"):
            display_df = df_filtered[[
                "date", "cbp_apprehended", "cbp_custody", "cbp_transfers",
                "hhs_care", "hhs_discharged", "total_system_load",
                "net_daily_intake", "backlog_indicator", "is_imputed", "has_anomaly",
            ]].copy()
            display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        f'<div class="page-footer">'
        f'UAC Program Capacity Monitor &nbsp;&middot;&nbsp;'
        f'HHS / Office of Refugee Resettlement &nbsp;&middot;&nbsp;'
        f'Data through {kpis_f["date_range_end"]}'
        f'</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

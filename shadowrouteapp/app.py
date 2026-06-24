"""
ShadowRoute: Privacy Exposure Analysis of Fitness Tracking Data
=============================================================
A cybersecurity and privacy research tool that evaluates GPS activity data
from fitness tracking applications to identify location privacy risks.

Research Question: To what extent can publicly shared fitness tracking data
expose sensitive personal information such as home locations, daily routines,
and frequently visited locations?
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import json
from pathlib import Path
from io import BytesIO
import base64

# Module imports
sys.path.insert(0, str(Path(__file__).parent))
from modules.parser import parse_multiple_gpx
from modules.home_detector import detect_home
from modules.route_analyzer import detect_repeated_routes, detect_routines, detect_frequent_locations
from modules.risk_calculator import calculate_privacy_score
from modules.recommendations import generate_recommendations
from modules.map_visualizer import build_map

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ShadowRoute · Privacy Analysis",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Base */
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;500;600;700&display=swap');

  :root {
    --bg-primary: #0a0d14;
    --bg-card: #111827;
    --bg-card-border: rgba(99,102,241,0.18);
    --accent: #6366f1;
    --accent-warn: #f59e0b;
    --accent-danger: #ef4444;
    --accent-safe: #22c55e;
    --text-primary: #f1f5f9;
    --text-muted: #94a3b8;
    --font-mono: 'JetBrains Mono', monospace;
    --font-body: 'Inter', sans-serif;
  }

  html, body, [class*="css"] {
    font-family: var(--font-body);
    background-color: var(--bg-primary);
    color: var(--text-primary);
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid rgba(99,102,241,0.15);
  }

  /* Metric cards */
  .metric-card {
    background: var(--bg-card);
    border: 1px solid var(--bg-card-border);
    border-radius: 12px;
    padding: 20px 22px;
    text-align: center;
    transition: border-color 0.2s;
  }
  .metric-card:hover { border-color: var(--accent); }
  .metric-label {
    font-size: 11px;
    font-family: var(--font-mono);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    margin-bottom: 8px;
  }
  .metric-value {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.1;
  }
  .metric-sub {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 4px;
  }

  /* Score gauge */
  .score-ring-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }
  .risk-badge {
    font-family: var(--font-mono);
    font-size: 13px;
    letter-spacing: 0.1em;
    padding: 4px 16px;
    border-radius: 100px;
    font-weight: 600;
  }

  /* Section headers */
  .section-header {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
    border-bottom: 1px solid rgba(255,255,255,0.07);
    padding-bottom: 8px;
    margin-bottom: 16px;
  }

  /* Recommendation cards */
  .rec-card {
    background: var(--bg-card);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 12px;
  }
  .rec-card.critical { border-left-color: var(--accent-danger); }
  .rec-card.high { border-left-color: var(--accent-warn); }
  .rec-card.medium { border-left-color: var(--accent); }
  .rec-card.low { border-left-color: #475569; }
  .rec-title {
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 6px;
  }
  .rec-desc {
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.6;
  }
  .rec-priority {
    font-family: var(--font-mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
    margin-bottom: 4px;
  }

  /* Finding rows */
  .finding-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
  }
  .finding-label { font-size: 13px; color: var(--text-muted); }
  .finding-value { font-family: var(--font-mono); font-size: 13px; font-weight: 600; }

  /* Upload area */
  [data-testid="stFileUploader"] {
    border: 1px dashed rgba(99,102,241,0.4) !important;
    border-radius: 12px;
    background: rgba(99,102,241,0.04);
  }

  /* Hide Streamlit branding */
  #MainMenu, footer { visibility: hidden; }
  .stDeployButton { display: none; }

  /* Progress bar */
  .breakdown-row {
    margin-bottom: 10px;
  }
  .breakdown-label {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    margin-bottom: 4px;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }
  .breakdown-bar-bg {
    background: rgba(255,255,255,0.06);
    border-radius: 4px;
    height: 8px;
    overflow: hidden;
  }
  .breakdown-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.6s ease;
  }

  /* Table styling */
  .route-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }
  .route-table th {
    font-family: var(--font-mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    text-align: left;
    padding: 8px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
  }
  .route-table td {
    padding: 9px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
  }
  .route-table tr:hover td { background: rgba(99,102,241,0.06); }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="margin-bottom:24px">
        <div style="font-family:'JetBrains Mono',monospace; font-size:20px; font-weight:700;
                    color:#6366f1; letter-spacing:-0.02em;">ShadowRoute</div>
        <div style="font-size:11px; color:#64748b; margin-top:2px; letter-spacing:0.05em;">
            PRIVACY EXPOSURE ANALYSIS
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Upload GPX Files")
    uploaded_files = st.file_uploader(
        "Select one or more .gpx files",
        type=["gpx"],
        accept_multiple_files=True,
        help="Export GPX files from Strava, Garmin Connect, Wahoo, or any fitness app.",
    )

    # Load sample data option
    st.markdown("---")
    use_samples = st.checkbox(
        "Use sample data",
        value=not bool(uploaded_files),
        help="Load pre-included sample GPX routes for demonstration.",
    )

    st.markdown("---")
    st.markdown("""
    <div style="font-size:11px; color:#475569; line-height:1.7;">
        <b style="color:#64748b">Research Context</b><br>
        This tool demonstrates how fitness tracking data can expose sensitive location
        intelligence including home addresses, daily routines, and movement patterns.
        <br><br>
        All analysis runs locally. No data is transmitted externally.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:10px; color:#334155; font-family:'JetBrains Mono',monospace;">
        ShadowRoute v1.0<br>
        Privacy Engineering Research
    </div>
    """, unsafe_allow_html=True)


# ── Load and parse files ───────────────────────────────────────────────────────
sample_dir = Path(__file__).parent / "sample_data"
files_to_parse = []

if uploaded_files:
    files_to_parse = uploaded_files
elif use_samples:
    files_to_parse = list(sample_dir.glob("*.gpx"))

if not files_to_parse:
    # Landing state
    st.markdown("""
    <div style="text-align:center; padding: 80px 40px;">
        <div style="font-size:52px; margin-bottom:16px;">🔒</div>
        <div style="font-size:28px; font-weight:700; color:#f1f5f9; margin-bottom:10px;">
            ShadowRoute
        </div>
        <div style="font-size:16px; color:#64748b; max-width:540px; margin:0 auto 24px; line-height:1.7;">
            Upload GPX files from your fitness app to analyse what location intelligence 
            your activity data exposes — home addresses, daily routines, and movement patterns.
        </div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:12px; color:#475569;
                    border:1px solid rgba(99,102,241,0.2); border-radius:8px;
                    display:inline-block; padding:8px 20px; background:rgba(99,102,241,0.05);">
            ← Upload .gpx files or enable sample data to begin
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ── Run analysis ───────────────────────────────────────────────────────────────
with st.spinner("Parsing GPX files…"):
    routes = parse_multiple_gpx(files_to_parse)

if not routes:
    st.error("No valid GPS data found in the uploaded files. Please check your GPX files.")
    st.stop()

with st.spinner("Running privacy analysis…"):
    home_result = detect_home(routes)
    repeated_result = detect_repeated_routes(routes)
    routine_result = detect_routines(routes)
    frequent_locations = detect_frequent_locations(routes)
    risk_score = calculate_privacy_score(
        home_result, repeated_result, routine_result, frequent_locations, len(routes)
    )
    recommendations = generate_recommendations(
        home_result, repeated_result, routine_result, frequent_locations, risk_score
    )
    folium_map = build_map(routes, home_result, frequent_locations)


# ── Header ─────────────────────────────────────────────────────────────────────
risk_colour = risk_score["risk_color"]
risk_level = risk_score["risk_level"]
total_score = risk_score["total_score"]

badge_bg = {"Low": "rgba(34,197,94,0.15)", "Medium": "rgba(245,158,11,0.15)", "High": "rgba(239,68,68,0.15)"}

st.markdown(f"""
<div style="display:flex; align-items:flex-start; justify-content:space-between;
            border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:24px; margin-bottom:28px;">
    <div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:22px; font-weight:700;
                    color:#6366f1; letter-spacing:-0.01em;">ShadowRoute</div>
        <div style="font-size:13px; color:#64748b; margin-top:2px;">
            Privacy Exposure Analysis · {len(routes)} route{'s' if len(routes) != 1 else ''} analysed
        </div>
    </div>
    <div style="text-align:right;">
        <div style="font-family:'JetBrains Mono',monospace; font-size:42px; font-weight:700;
                    color:{risk_colour}; line-height:1;">{total_score}</div>
        <div style="font-size:11px; color:#64748b; margin-top:2px;">/ 100 EXPOSURE SCORE</div>
        <div style="display:inline-block; margin-top:6px; padding:3px 14px;
                    background:{badge_bg[risk_level]}; border:1px solid {risk_colour}40;
                    border-radius:100px; font-family:'JetBrains Mono',monospace;
                    font-size:11px; font-weight:700; color:{risk_colour}; letter-spacing:0.1em;">
            {risk_level.upper()} RISK
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Top metrics ────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

total_distance = sum(r.get("total_distance_km", 0) for r in routes)
total_points = sum(r.get("point_count", 0) for r in routes)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Routes</div>
        <div class="metric-value" style="color:#6366f1">{len(routes)}</div>
        <div class="metric-sub">files parsed</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">GPS Points</div>
        <div class="metric-value" style="color:#6366f1">{total_points:,}</div>
        <div class="metric-sub">coordinates extracted</div>
    </div>""", unsafe_allow_html=True)

with col3:
    home_conf = f"{home_result['confidence']}%" if home_result.get("detected") else "—"
    home_colour = "#ef4444" if home_result.get("detected") else "#475569"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Home Detected</div>
        <div class="metric-value" style="color:{home_colour}">{home_conf}</div>
        <div class="metric-sub">confidence</div>
    </div>""", unsafe_allow_html=True)

with col4:
    rep = repeated_result.get("repeated_count", 0)
    rep_col = "#f59e0b" if rep > 0 else "#475569"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Repeated Routes</div>
        <div class="metric-value" style="color:{rep_col}">{rep}</div>
        <div class="metric-sub">instances detected</div>
    </div>""", unsafe_allow_html=True)

with col5:
    rl = routine_result.get("routine_level", "Unknown")
    rl_col = {"Low": "#22c55e", "Medium": "#f59e0b", "High": "#ef4444", "Unknown": "#475569"}[rl]
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Routine Level</div>
        <div class="metric-value" style="color:{rl_col}">{rl}</div>
        <div class="metric-sub">predictability</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_map, tab_analysis, tab_routes, tab_recs = st.tabs([
    "🗺️  Route Map",
    "📊  Analysis",
    "📋  Route Details",
    "🛡️  Recommendations",
])


# ─────────────────────────────────────────────────────────────────
# TAB: Route Map
# ─────────────────────────────────────────────────────────────────
with tab_map:
    st.markdown('<div class="section-header">Interactive Route Visualisation</div>', unsafe_allow_html=True)

    try:
        from streamlit_folium import st_folium
        st_folium(folium_map, width="100%", height=540, returned_objects=[])
    except ImportError:
        # Fallback: render as HTML component
        map_html = folium_map._repr_html_()
        st.components.v1.html(map_html, height=540, scrolling=False)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(f"""
        <div style="background:#111827; border:1px solid rgba(34,197,94,0.3); border-radius:8px;
                    padding:12px 16px; font-size:12px; color:#64748b;">
            <span style="color:#22c55e">●</span> Green markers = route start points<br>
            <span style="color:#ef4444">●</span> Red markers = route end points
        </div>""", unsafe_allow_html=True)
    with col_b:
        if home_result.get("detected"):
            st.markdown(f"""
            <div style="background:#111827; border:1px solid rgba(239,68,68,0.3); border-radius:8px;
                        padding:12px 16px; font-size:12px; color:#64748b;">
                <span style="color:#ef4444">🏠</span> Red pin = probable home location<br>
                Red circle = recommended 300m privacy zone
            </div>""", unsafe_allow_html=True)
    with col_c:
        if frequent_locations:
            st.markdown(f"""
            <div style="background:#111827; border:1px solid rgba(245,158,11,0.3); border-radius:8px;
                        padding:12px 16px; font-size:12px; color:#64748b;">
                <span style="color:#f59e0b">●</span> Amber markers = frequent location clusters<br>
                ({len(frequent_locations)} cluster{'s' if len(frequent_locations) != 1 else ''} identified)
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# TAB: Analysis
# ─────────────────────────────────────────────────────────────────
with tab_analysis:
    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        # Score breakdown
        st.markdown('<div class="section-header">Privacy Exposure Score Breakdown</div>', unsafe_allow_html=True)

        breakdown = risk_score["breakdown"]
        weights = {
            "home_exposure": 40,
            "repeated_routes": 25,
            "routine_detection": 20,
            "frequent_locations": 15,
        }
        labels = {
            "home_exposure": "Home Exposure",
            "repeated_routes": "Repeated Routes",
            "routine_detection": "Routine Detection",
            "frequent_locations": "Frequent Locations",
        }
        bar_colours = {
            "home_exposure": "#ef4444",
            "repeated_routes": "#f59e0b",
            "routine_detection": "#6366f1",
            "frequent_locations": "#10b981",
        }

        for key, max_pts in weights.items():
            score_val = breakdown[key]
            pct = (score_val / max_pts * 100) if max_pts > 0 else 0
            col_bar = bar_colours[key]
            st.markdown(f"""
            <div class="breakdown-row">
                <div class="breakdown-label">
                    <span>{labels[key]}</span>
                    <span>{score_val} / {max_pts} pts</span>
                </div>
                <div class="breakdown-bar-bg">
                    <div class="breakdown-bar-fill" style="width:{pct}%; background:{col_bar};"></div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin-top:20px; padding:16px; background:#111827;
                    border:1px solid {risk_colour}30; border-radius:10px; text-align:center;">
            <div style="font-family:'JetBrains Mono',monospace; font-size:36px; font-weight:700;
                        color:{risk_colour};">{total_score}</div>
            <div style="font-size:11px; color:#64748b; margin-top:2px;">TOTAL EXPOSURE SCORE</div>
            <div style="margin-top:8px; font-size:12px; color:{risk_colour}; font-weight:600;">
                {risk_score['risk_emoji']} {risk_level} Risk
            </div>
        </div>""", unsafe_allow_html=True)

    with right_col:
        # Home detection
        st.markdown('<div class="section-header">Home Location Detection</div>', unsafe_allow_html=True)
        if home_result.get("detected"):
            st.markdown(f"""
            <div style="background:#1c0f0f; border:1px solid rgba(239,68,68,0.3); border-radius:10px; padding:16px;">
                <div style="color:#ef4444; font-weight:700; margin-bottom:10px;">⚠️ Probable Residence Detected</div>
                <div class="finding-row">
                    <span class="finding-label">Confidence</span>
                    <span class="finding-value" style="color:#ef4444">{home_result['confidence']}%</span>
                </div>
                <div class="finding-row">
                    <span class="finding-label">Endpoint cluster size</span>
                    <span class="finding-value">{home_result['cluster_size']}</span>
                </div>
                <div class="finding-row">
                    <span class="finding-label">Lat / Lon</span>
                    <span class="finding-value" style="font-size:11px;">
                        {home_result['latitude']:.4f}, {home_result['longitude']:.4f}
                    </span>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#0d1a0d; border:1px solid rgba(34,197,94,0.3); border-radius:10px; padding:16px;">
                <div style="color:#22c55e; font-weight:700;">✓ No Home Location Detected</div>
                <div style="font-size:12px; color:#64748b; margin-top:6px;">
                    Insufficient clustering in route endpoints to identify a probable residence.
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Routine analysis
        st.markdown('<div class="section-header">Routine & Pattern Analysis</div>', unsafe_allow_html=True)
        rl_col2 = {"Low": "#22c55e", "Medium": "#f59e0b", "High": "#ef4444", "Unknown": "#475569"}[routine_result.get("routine_level", "Unknown")]
        st.markdown(f"""
        <div style="background:#111827; border:1px solid rgba(255,255,255,0.07); border-radius:10px; padding:16px;">
            <div class="finding-row">
                <span class="finding-label">Routine Level</span>
                <span class="finding-value" style="color:{rl_col2}">{routine_result.get('routine_level', 'Unknown')}</span>
            </div>
            <div class="finding-row">
                <span class="finding-label">Peak Activity Hour</span>
                <span class="finding-value">
                    {f"{routine_result['peak_hour']:02d}:00" if routine_result.get('peak_hour') is not None else '—'}
                </span>
            </div>
            <div class="finding-row">
                <span class="finding-label">Most Active Day</span>
                <span class="finding-value">{routine_result.get('dominant_weekday') or '—'}</span>
            </div>
        </div>""", unsafe_allow_html=True)

        patterns = routine_result.get("patterns", [])
        if patterns:
            st.markdown("<br>", unsafe_allow_html=True)
            for p in patterns:
                st.markdown(f"""
                <div style="font-size:12px; color:#94a3b8; padding:6px 12px;
                            background:rgba(99,102,241,0.06); border-radius:6px; margin-bottom:6px;
                            border-left:2px solid #6366f1;">
                    {p}
                </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Repeated routes & frequent locations
    col_rep, col_freq = st.columns(2, gap="large")

    with col_rep:
        st.markdown('<div class="section-header">Repeated Route Detection</div>', unsafe_allow_html=True)
        groups = repeated_result.get("repeated_groups", [])
        if groups:
            for i, group in enumerate(groups):
                st.markdown(f"""
                <div style="background:#1a1400; border:1px solid rgba(245,158,11,0.25);
                            border-radius:8px; padding:12px 14px; margin-bottom:8px;">
                    <div style="font-size:11px; color:#f59e0b; font-family:'JetBrains Mono',monospace;
                                margin-bottom:6px;">REPEATED GROUP {i+1} · {len(group)} occurrences</div>
                    {''.join(f'<div style="font-size:12px; color:#94a3b8; padding:2px 0;">• {name}</div>' for name in group)}
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#0d1a0d; border:1px solid rgba(34,197,94,0.2); border-radius:8px;
                        padding:12px 14px; font-size:12px; color:#22c55e;">
                ✓ No significantly repeated routes detected.
            </div>""", unsafe_allow_html=True)

    with col_freq:
        st.markdown('<div class="section-header">Frequent Location Clusters</div>', unsafe_allow_html=True)
        if frequent_locations:
            for loc in frequent_locations:
                st.markdown(f"""
                <div style="background:#111827; border:1px solid rgba(245,158,11,0.2);
                            border-radius:8px; padding:10px 14px; margin-bottom:8px;
                            display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-size:13px; font-weight:600; color:#f1f5f9;">
                            {loc['label']}
                        </div>
                        <div style="font-size:11px; color:#64748b; font-family:'JetBrains Mono',monospace; margin-top:2px;">
                            {loc['latitude']:.4f}, {loc['longitude']:.4f}
                        </div>
                    </div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:18px;
                                font-weight:700; color:#f59e0b;">
                        {loc['visit_count']}
                        <div style="font-size:9px; color:#64748b; font-weight:400;">visits</div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#111827; border:1px solid rgba(255,255,255,0.07);
                        border-radius:8px; padding:12px 14px; font-size:12px; color:#64748b;">
                No significant frequent location clusters identified.
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# TAB: Route Details
# ─────────────────────────────────────────────────────────────────
with tab_routes:
    st.markdown('<div class="section-header">Parsed Route Summary</div>', unsafe_allow_html=True)

    rows = []
    for r in routes:
        st_time = r.get("start_time")
        rows.append({
            "Route Name": r.get("name", "Unknown"),
            "Date": st_time.date().isoformat() if st_time else "—",
            "Start Time": f"{st_time.hour:02d}:{st_time.minute:02d}" if st_time else "—",
            "Distance (km)": r.get("total_distance_km", "—"),
            "Duration (min)": r.get("duration_minutes", "—"),
            "GPS Points": r.get("point_count", 0),
            "Start Lat": f"{r['start_point'][0]:.4f}" if r.get("start_point") else "—",
            "Start Lon": f"{r['start_point'][1]:.4f}" if r.get("start_point") else "—",
        })

    df_routes = pd.DataFrame(rows)

    # Render as styled HTML table
    table_rows = ""
    for _, row in df_routes.iterrows():
        table_rows += "<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>"

    headers = "".join(f"<th>{c}</th>" for c in df_routes.columns)
    st.markdown(f"""
    <table class="route-table">
        <thead><tr>{headers}</tr></thead>
        <tbody>{table_rows}</tbody>
    </table>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Research Dataset Evaluation</div>', unsafe_allow_html=True)

    metrics = [
        ("Home Location Detected", "✓" if home_result.get("detected") else "✗", "#ef4444" if home_result.get("detected") else "#22c55e"),
        ("Repeated Routes Found", "✓" if repeated_result.get("repeated_count", 0) > 0 else "✗",
         "#f59e0b" if repeated_result.get("repeated_count", 0) > 0 else "#22c55e"),
        ("Routine Detected", "✓" if routine_result.get("routine_level") in ("Medium", "High") else "✗",
         "#f59e0b" if routine_result.get("routine_level") in ("Medium", "High") else "#22c55e"),
        ("Risk Classification", risk_level, risk_colour),
        ("Location Clusters", str(len(frequent_locations)), "#f59e0b" if frequent_locations else "#22c55e"),
    ]

    eval_cols = st.columns(len(metrics))
    for col, (label, value, colour) in zip(eval_cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="color:{colour}; font-size:1.5rem;">{value}</div>
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# TAB: Recommendations
# ─────────────────────────────────────────────────────────────────
with tab_recs:
    st.markdown('<div class="section-header">Privacy Recommendations</div>', unsafe_allow_html=True)

    priority_colours = {
        "Critical": "#ef4444",
        "High": "#f59e0b",
        "Medium": "#6366f1",
        "Low": "#475569",
    }
    priority_css = {
        "Critical": "critical",
        "High": "high",
        "Medium": "medium",
        "Low": "low",
    }

    for rec in recommendations:
        pri = rec["priority"]
        colour = priority_colours.get(pri, "#6366f1")
        css_cls = priority_css.get(pri, "medium")
        st.markdown(f"""
        <div class="rec-card {css_cls}">
            <div class="rec-priority" style="color:{colour}">{pri}</div>
            <div class="rec-title">{rec['icon']} {rec['title']}</div>
            <div class="rec-desc">{rec['description']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(99,102,241,0.05); border:1px solid rgba(99,102,241,0.15);
                border-radius:10px; padding:20px; font-size:12px; color:#64748b; line-height:1.8;">
        <b style="color:#94a3b8">Research Note</b><br>
        This analysis demonstrates the privacy risks inherent in sharing fitness tracking data. 
        Seemingly harmless activity logs can be combined to reveal sensitive personal information 
        including home addresses, workplace locations, and predictable daily schedules. 
        This type of analysis is employed by security researchers, OSINT practitioners, 
        and adversaries alike — reinforcing the importance of privacy-by-default settings 
        in fitness applications.
    </div>""", unsafe_allow_html=True)

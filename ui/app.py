"""RCC Simulation Dashboard — Streamlit entry point."""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `from src...` imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Kidney Cancer Simulator",
    page_icon="\U0001f9ec",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

_CSS = """
<style>
/* ---- Global polish ---- */
.main .block-container {
    padding-top: 2rem;
}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A2332 0%, #0F1922 100%);
}
[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stSelectbox label {
    color: #94A3B8 !important;
}

/* ---- Page headers ---- */
h1 {
    color: #0D7377 !important;
    border-bottom: 3px solid #0D7377;
    padding-bottom: 0.3rem;
}
h2 {
    color: #1A2332 !important;
    border-bottom: 1px solid #CBD5E1;
    padding-bottom: 0.2rem;
}

/* ---- Metric cards ---- */
[data-testid="stMetric"] {
    background-color: #F0F4F8;
    border-radius: 10px;
    padding: 14px 18px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 3px 8px rgba(0,0,0,0.08);
}
[data-testid="stMetric"] label {
    color: #64748B !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.03em;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #1A2332 !important;
    font-weight: 600 !important;
}

/* ---- Outcome badges ---- */
.badge-survival,
.badge-progression,
.badge-unknown {
    display: inline-block;
    padding: 10px 28px;
    border-radius: 9999px;
    font-weight: 700;
    font-size: 1.3rem;
    letter-spacing: 0.08em;
    color: white !important;
}
.badge-survival {
    background: linear-gradient(135deg, #059669, #10B981);
    box-shadow: 0 4px 14px rgba(5, 150, 105, 0.35);
}
.badge-progression {
    background: linear-gradient(135deg, #DC2626, #EF4444);
    box-shadow: 0 4px 14px rgba(220, 38, 38, 0.35);
}
.badge-unknown {
    background: linear-gradient(135deg, #6B7280, #9CA3AF);
    box-shadow: 0 4px 14px rgba(107, 114, 128, 0.35);
}

/* ---- Buttons ---- */
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    transition: transform 0.1s ease;
}
.stButton > button:active {
    transform: scale(0.98);
}

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #F8FAFC;
    border-radius: 8px 8px 0 0;
    padding: 4px 4px 0 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px 6px 0 0;
    padding: 8px 20px;
}

/* ---- Expanders ---- */
[data-testid="stExpander"] {
    border-radius: 8px;
    border: 1px solid #E2E8F0;
}

/* ---- Info cards ---- */
.info-card {
    background: #F0F4F8;
    border-left: 4px solid #0D7377;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.info-card-warn {
    background: #FFFBEB;
    border-left: 4px solid #F59E0B;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-bottom: 8px;
}

/* ---- Treatment badge ---- */
.treatment-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.85rem;
}
.treatment-ici { background: #DBEAFE; color: #1E40AF !important; }
.treatment-tki { background: #FEE2E2; color: #991B1B !important; }
.treatment-combo { background: #F3E8FF; color: #6B21A8 !important; }
.treatment-none { background: #F1F5F9; color: #64748B !important; }

/* ---- Scenario preset cards ---- */
.scenario-card {
    background: white;
    border: 2px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.2s ease;
    height: 100%;
}
.scenario-card:hover {
    border-color: #0D7377;
    box-shadow: 0 4px 12px rgba(13, 115, 119, 0.15);
    transform: translateY(-2px);
}
.scenario-card.active {
    border-color: #0D7377;
    background: #F0F9FF;
}
.scenario-card h5 {
    color: #0D7377 !important;
    margin: 0 0 6px 0 !important;
    border: none !important;
}
.scenario-card p {
    color: #64748B;
    font-size: 0.82rem;
    margin: 0;
    line-height: 1.4;
}
.scenario-card .outcome-hint {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-top: 8px;
}
.scenario-card .outcome-survival { background: #D1FAE5; color: #065F46; }
.scenario-card .outcome-progression { background: #FEE2E2; color: #991B1B; }
.scenario-card .outcome-stable { background: #DBEAFE; color: #1E40AF; }
.scenario-card .outcome-variable { background: #FEF3C7; color: #92400E; }

/* ---- Cell color legend ---- */
.cell-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 16px;
    padding: 8px 12px;
    background: rgba(15, 23, 42, 0.95);
    border-radius: 8px;
    border: 1px solid rgba(14, 230, 183, 0.15);
}
.cell-legend-item {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 0.72rem;
    color: #94A3B8;
    font-family: 'JetBrains Mono', monospace;
}
.cell-legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

/* ---- Review config card ---- */
.review-card {
    background: linear-gradient(135deg, #F0F9FF, #F0F4F8);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #CBD5E1;
}
.review-card h5 {
    color: #0D7377 !important;
    margin: 0 0 8px 0 !important;
    border: none !important;
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
.review-card .review-line {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    border-bottom: 1px solid rgba(0,0,0,0.05);
}
.review-card .review-line:last-child { border-bottom: none; }
.review-card .review-label {
    color: #64748B;
    font-size: 0.85rem;
}
.review-card .review-value {
    color: #1A2332;
    font-weight: 600;
    font-size: 0.85rem;
}

/* ---- HUD simulation dashboard ---- */
.hud-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 18px;
    background: linear-gradient(90deg, rgba(13,115,119,0.2), rgba(13,115,119,0.05), transparent);
    border-left: 3px solid #0D7377;
    border-radius: 0 8px 8px 0;
    margin-bottom: 12px;
}
.hud-title {
    color: #0EE6B7 !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin: 0 !important;
    border: none !important;
}
.hud-panel {
    background: rgba(15, 23, 42, 0.95);
    border: 1px solid rgba(14, 230, 183, 0.2);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 8px;
}
.hud-panel-title {
    color: #0EE6B7 !important;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 0 0 8px 0 !important;
    border: none !important;
    padding: 0 !important;
}
.hud-stat {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 4px 0;
    border-bottom: 1px solid rgba(14,230,183,0.07);
}
.hud-stat:last-child { border-bottom: none; }
.hud-stat-label {
    color: #94A3B8;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
}
.hud-stat-value {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 0.95rem;
}
.hud-stat-value.tumor { color: #EF4444; }
.hud-stat-value.immune { color: #3B82F6; }
.hud-stat-value.glucose { color: #F59E0B; }
.hud-stat-value.neutral { color: #E2E8F0; }
.hud-stat-value.good { color: #10B981; }
.hud-stat-value.bad { color: #EF4444; }
.hud-stat-delta {
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    margin-left: 6px;
}
.hud-stat-delta.up { color: #EF4444; }
.hud-stat-delta.down { color: #10B981; }

@keyframes hud-pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 4px rgba(14,230,183,0.3); }
    50% { opacity: 0.7; box-shadow: 0 0 12px rgba(14,230,183,0.6); }
}
.hud-live-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #0EE6B7;
    animation: hud-pulse 1.5s ease-in-out infinite;
    margin-right: 8px;
}
@keyframes hud-scan {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
.hud-scan-line {
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(14,230,183,0.5), transparent);
    background-size: 200% 100%;
    animation: hud-scan 3s linear infinite;
    margin: 6px 0;
    border-radius: 1px;
}

/* ---- Primary buttons ---- */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0D7377, #10B981) !important;
    border: none !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em;
    font-size: 1rem !important;
    padding: 0.6rem 1.5rem !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 14px rgba(13, 115, 119, 0.3) !important;
}

/* ---- Bordered containers ---- */
[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px !important;
    border-color: #E2E8F0 !important;
    transition: box-shadow 0.15s ease;
}
[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* ---- Progress bar ---- */
[data-testid="stProgress"] > div > div > div {
    background: linear-gradient(90deg, #0D7377, #10B981) !important;
    border-radius: 999px;
}

/* ---- Treatment selector cards ---- */
.treatment-card {
    background: white;
    border: 2px solid #E2E8F0;
    border-radius: 12px;
    padding: 14px 16px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: center;
    height: 100%;
}
.treatment-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.treatment-card.selected {
    border-color: #0D7377;
    background: #F0FDFA;
    box-shadow: 0 0 0 1px #0D7377;
}
.treatment-card .tc-icon {
    font-size: 1.6rem;
    margin-bottom: 4px;
}
.treatment-card .tc-name {
    font-weight: 700;
    color: #1A2332;
    font-size: 0.9rem;
    margin: 2px 0;
}
.treatment-card .tc-desc {
    color: #64748B;
    font-size: 0.75rem;
    line-height: 1.4;
}

/* ---- Outcome labels (friendly text) ---- */
.outcome-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.8rem;
}
.outcome-pill-survival { background: #D1FAE5; color: #065F46; }
.outcome-pill-progression { background: #FEE2E2; color: #991B1B; }
.outcome-pill-unknown { background: #F1F5F9; color: #64748B; }

/* ---- Dataframe styling ---- */
[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
}

/* ---- Welcome page ---- */
.welcome-hero {
    text-align: center;
    padding: 48px 24px;
    background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 30%, #F0F4F8 100%);
    border-radius: 16px;
    border: 1px solid #BAE6FD;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.welcome-hero::before {
    content: "";
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 30% 40%, rgba(13,115,119,0.06) 0%, transparent 50%),
                radial-gradient(circle at 70% 60%, rgba(16,185,129,0.06) 0%, transparent 50%);
    animation: hero-float 8s ease-in-out infinite alternate;
}
@keyframes hero-float {
    0% { transform: translate(0, 0); }
    100% { transform: translate(20px, -10px); }
}
.welcome-hero h2 {
    color: #0D7377 !important;
    border: none !important;
    font-size: 2rem !important;
    margin-bottom: 12px !important;
    position: relative;
}
.welcome-hero p {
    color: #475569;
    font-size: 1.1rem;
    max-width: 650px;
    margin: 0 auto;
    line-height: 1.6;
    position: relative;
}
.workflow-step {
    background: white;
    border-radius: 12px;
    padding: 24px 20px;
    border: 1px solid #E2E8F0;
    text-align: center;
    height: 100%;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.workflow-step:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}
.workflow-step .step-number {
    display: inline-block;
    width: 36px;
    height: 36px;
    line-height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #0D7377, #10B981);
    color: white !important;
    font-weight: 700;
    font-size: 1rem;
    margin-bottom: 10px;
}
.workflow-step h4 {
    color: #1A2332 !important;
    margin: 4px 0 8px 0 !important;
}
.workflow-step p {
    color: #64748B;
    font-size: 0.85rem;
    margin: 0;
    line-height: 1.5;
}
</style>
"""

st.markdown(_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

home_page = st.Page("pages/0_home.py", title="Home", icon=":material/home:")
configure_page = st.Page("pages/1_configure.py", title="Set Up", icon=":material/settings:")
run_page = st.Page("pages/2_run.py", title="Run", icon=":material/play_arrow:")
results_page = st.Page("pages/3_results.py", title="Results", icon=":material/show_chart:")
history_page = st.Page("pages/4_history.py", title="Compare", icon=":material/compare:")
environment_page = st.Page("pages/5_environment.py", title="3D View", icon=":material/view_in_ar:")
glucose_page = st.Page("pages/7_glucose.py", title="Glucose Field", icon=":material/water_drop:")
about_page = st.Page("pages/6_about.py", title="About", icon=":material/info:")

pg = st.navigation([home_page, configure_page, run_page, results_page, history_page, environment_page, glucose_page, about_page])

# Sidebar branding & status
with st.sidebar:
    st.markdown("### Kidney Cancer Simulator")
    st.caption("Tumor vs Immune System")
    st.divider()

    # Show quick status of last run if available
    if "last_run_meta" in st.session_state:
        from ui.lib.formatting import outcome_badge_html
        meta = st.session_state["last_run_meta"]
        outcome = meta.get("outcome", "?")
        badge = outcome_badge_html(outcome, font_size="0.8rem", padding="3px 10px")
        st.markdown(f'<div style="text-align:center">{badge}</div>', unsafe_allow_html=True)
        _TREATMENT_MAP = {"None": "Untreated", "ICI": "Immunotherapy",
                          "TKI": "Targeted therapy", "ICI+TKI": "Combination"}
        treatment = _TREATMENT_MAP.get(meta.get("treatment", "?"), meta.get("treatment", "?"))
        elapsed = meta.get("elapsed_seconds", 0)
        st.caption(f"Last run: {treatment}, {elapsed:.0f}s")
        st.divider()

    # Current setup summary (if params exist)
    if "params" in st.session_state:
        _p = st.session_state["params"]
        _trt_map = {"None": "Untreated", "ICI": "Immunotherapy",
                     "TKI": "Targeted", "ICI+TKI": "Combo"}
        _sex = "F" if _p.get("sex") == "F" else "M"
        st.caption(
            f"**Current setup:**\n"
            f"- {_trt_map.get(_p.get('treatment', '?'), '?')} "
            f"at step {_p.get('treatment_start', '?')}\n"
            f"- {'Female' if _sex == 'F' else 'Male'}, "
            f"BMI {_p.get('BMI', '?')}\n"
            f"- {_p.get('max_steps', '?')} steps"
        )
        st.divider()

    # Quick reference
    st.caption("**How to use:**")
    st.caption("1. **Set Up** your patient & treatment\n"
               "2. **Run** the simulation\n"
               "3. See **Results** and **3D View**\n"
               "4. **Compare** different treatments")
    st.divider()

pg.run()

# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Simulation execution — live dashboard with 3D visualization.

Monitors the battle between tumor and immune cells in real time,
showing population dynamics, 3D snapshots, and outcome detection.
"""

import copy
import time
import zipfile
from collections import deque
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from ui.lib.state import (
    load_all_defaults, get_dimension_from_volume,
    load_run_csv, load_snapshot, latest_snapshot, snapshot_dir_for,
    list_snapshot_steps,
)
from ui.lib.charts import (
    environment_3d, spatial_density_map,
    population_dynamics, tumor_growth, kill_counts,
    glucose_dashboard, immune_effectiveness_pie,
    CELL_COLORS, KILL_COLORS, KILL_COLS, NON_CELL_COLS,
    AgentType, AGENT_TYPE_VIS, NON_IMMUNE,
)
from ui.lib.formatting import (
    format_sex, render_outcome_badge, TREATMENT_INFO, TREATMENT_LABELS,
    format_column_name, format_kill_column_name,
)
from ui.lib.runner import start_simulation, parse_progress_line, finalize_run, cancel_simulation, check_timeout

_SNAPSHOT_INTERVAL = 10
_CHART_UPDATE_INTERVAL = 5
# Critical mass threshold — kept in sync with engine (rcc_model.py:56)
_CRITICAL_MASS = 2000

# Dark HUD chart layout
_HUD_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(11,17,32,0)",
    plot_bgcolor="rgba(15,23,42,0.6)",
    font=dict(family="JetBrains Mono, Fira Code, monospace", color="#94A3B8", size=10),
    margin=dict(l=45, r=15, t=30, b=30),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(size=9, color="#94A3B8")),
    xaxis=dict(gridcolor="rgba(14,230,183,0.07)", zerolinecolor="rgba(14,230,183,0.1)"),
    yaxis=dict(gridcolor="rgba(14,230,183,0.07)", zerolinecolor="rgba(14,230,183,0.1)"),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _termination_reason(hist_tumor, initial_tumor):
    """Return a human-readable reason for early simulation termination."""
    if not hist_tumor:
        return "Simulation complete"
    final = hist_tumor[-1]
    if final == 0:
        return "All tumor cells eliminated — Survival"
    if final >= _CRITICAL_MASS:
        return "Tumor exceeded critical mass — Progression"
    return "Terminal condition reached"


def _status_message(tumor, initial_tumor, immune, step, treatment_start):
    """Dynamic 1-sentence summary of what's happening right now."""
    if tumor == 0:
        return "The immune system has eliminated all tumor cells."
    ratio = immune / max(1, tumor)
    if ratio > 2:
        return "Strong immune response — the tumor is under heavy attack."
    if ratio > 1:
        return "Immune cells outnumber tumor cells — treatment is helping."
    if tumor > (initial_tumor or tumor) * 1.5:
        return "The tumor is growing rapidly — immune response may not be enough."
    if treatment_start is not None and step < treatment_start:
        return "Pre-treatment phase — the tumor is growing against natural immunity."
    return "Treatment is active — monitoring the immune-tumor battle."


def _hud_tumor_chart(steps_list, tumor_list, treatment_start=None,
                     termination_step=None):
    """Tumor cell count over time."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=steps_list, y=tumor_list,
        name="Tumor cells", line=dict(color="#EF4444", width=2.5),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.1)",
        hovertemplate="Tumor: %{y:,.0f}<extra></extra>",
    ))
    # Critical mass threshold line
    fig.add_hline(y=_CRITICAL_MASS, line_dash="dash", line_color="rgba(148,163,184,0.4)",
                  line_width=1,
                  annotation_text=f"Critical mass ({_CRITICAL_MASS:,})",
                  annotation_font_color="#94A3B8",
                  annotation_font_size=9,
                  annotation_position="top left")
    # Treatment onset
    if treatment_start is not None and steps_list and treatment_start <= steps_list[-1]:
        fig.add_vrect(x0=treatment_start, x1=max(steps_list),
                      fillcolor="rgba(14,230,183,0.04)", line_width=0)
        fig.add_vline(x=treatment_start, line_dash="dash",
                      line_color="rgba(14,230,183,0.5)", line_width=1.5,
                      annotation_text="Treatment starts",
                      annotation_font_color="#0EE6B7",
                      annotation_font_size=9)
    # Termination marker
    if termination_step is not None:
        fig.add_vline(x=termination_step, line_dash="dash",
                      line_color="rgba(239,68,68,0.7)", line_width=1.5,
                      annotation_text="Ended",
                      annotation_font_color="#EF4444",
                      annotation_font_size=9)
    layout = copy.deepcopy(_HUD_LAYOUT)
    layout.update(
        title=dict(text="TUMOR CELLS", font=dict(size=11, color="#EF4444")),
        height=320, xaxis_title="Step",
        yaxis=dict(title=dict(text="Cell count"),
                   gridcolor="rgba(14,230,183,0.07)"),
    )
    fig.update_layout(**layout)
    return fig


def _hud_immune_chart(steps_list, tumor_list, immune_list,
                      treatment_start=None):
    """Immune vs tumor cell count comparison."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=steps_list, y=immune_list, name="Immune cells",
        fill="tozeroy", fillcolor="rgba(59,130,246,0.15)",
        line=dict(color="#3B82F6", width=2),
        hovertemplate="Immune: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=steps_list, y=tumor_list, name="Tumor cells",
        line=dict(color="#EF4444", width=1.5, dash="dot"),
        hovertemplate="Tumor: %{y:,.0f}<extra></extra>",
    ))
    if treatment_start is not None and steps_list and treatment_start <= steps_list[-1]:
        fig.add_vline(x=treatment_start, line_dash="dash",
                      line_color="rgba(14,230,183,0.5)", line_width=1.5,
                      annotation_text="Treatment starts",
                      annotation_font_color="#0EE6B7",
                      annotation_font_size=9)
    layout = copy.deepcopy(_HUD_LAYOUT)
    layout.update(
        title=dict(text="IMMUNE vs TUMOR", font=dict(size=11, color="#3B82F6")),
        height=320, xaxis_title="Step", yaxis_title="Cell count",
    )
    fig.update_layout(**layout)
    return fig


def _hud_glucose_chart(steps_list, glucose_list):
    """Glucose (energy) level over time."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=steps_list, y=glucose_list,
        name="Glucose", line=dict(color="#F59E0B", width=2),
        fill="tozeroy", fillcolor="rgba(245,158,11,0.1)",
        hovertemplate="%{y:.3f}",
    ))
    if glucose_list:
        fig.add_hline(y=glucose_list[0], line_dash="dot",
                      line_color="rgba(245,158,11,0.4)", line_width=1,
                      annotation_text="Starting level",
                      annotation_font_color="#F59E0B",
                      annotation_font_size=9)
    layout = copy.deepcopy(_HUD_LAYOUT)
    layout.update(
        title=dict(text="GLUCOSE (ENERGY)", font=dict(size=11, color="#F59E0B")),
        height=300, showlegend=True, xaxis_title="Step",
        yaxis_title="Concentration",
    )
    fig.update_layout(**layout)
    return fig


def _hud_stat(label, value, css_class="neutral", delta=None):
    """Single stat line HTML."""
    delta_html = ""
    if delta is not None and delta != 0:
        d_class = "up" if delta > 0 else "down"
        delta_html = f'<span class="hud-stat-delta {d_class}">{delta:+,}</span>'
    return (
        f'<div class="hud-stat">'
        f'<span class="hud-stat-label">{label}</span>'
        f'<span class="hud-stat-value {css_class}">{value}{delta_html}</span>'
        f'</div>'
    )


def _render_snapshot(path, container, chart_key,
                     visible_types=None, marker_size=3, camera=None):
    """Load and render 3D snapshot."""
    try:
        snap = load_snapshot(path)
        fig = environment_3d(
            agents=snap["agents"], glucose=snap["glucose"],
            grid_dims=snap["grid_dims"], dark_mode=True,
            visible_types=visible_types, marker_size=marker_size,
        )
        fig.update_layout(height=500)
        if camera is not None:
            fig.update_layout(scene_camera=camera)
        container.plotly_chart(fig, use_container_width=True, key=chart_key)
    except (EOFError, OSError, ValueError, zipfile.BadZipFile):
        pass


def _render_density_map(path, container, chart_key):
    """Load snapshot and render 2D spatial density projection."""
    try:
        snap = load_snapshot(path)
        fig = spatial_density_map(
            agents=snap["agents"], glucose=snap["glucose"],
            grid_dims=snap["grid_dims"], dark_mode=True,
        )
        container.plotly_chart(fig, use_container_width=True, key=chart_key)
    except (EOFError, OSError, ValueError, zipfile.BadZipFile):
        pass


# =========================================================================
# PAGE START
# =========================================================================

st.title("▶️ Run Simulation")
st.caption("Watch the epic battle between tumor cells and the immune system unfold in real time. "
           "See population dynamics, glucose competition, and treatment effects as they happen.")

if "params" not in st.session_state:
    st.session_state["params"] = load_all_defaults()

params = st.session_state["params"]

if "run_active" not in st.session_state:
    st.session_state["run_active"] = False

# =========================================================================
# PHASE 1: PRE-RUN — Review & Launch
# =========================================================================

if not st.session_state["run_active"]:
    st.session_state["snapshot_interval"] = _SNAPSHOT_INTERVAL

    st.subheader("Ready to Launch")
    st.caption("Review your setup below. The simulation will run and show live results — 3D view, charts, and outcome.")

    treatment = params["treatment"]
    dim = get_dimension_from_volume(params["volume"], params.get("block_size", 10))

    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        st.markdown(
            '<div class="review-card" role="group" aria-label="Patient settings">'
            '<h5>Patient</h5>'
            f'<div class="review-line"><span class="review-label">Sex</span>'
            f'<span class="review-value">{format_sex(params["sex"])}</span></div>'
            f'<div class="review-line"><span class="review-label">BMI</span>'
            f'<span class="review-value">{params["BMI"]:.1f} kg/m\u00b2</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with pc2:
        st.markdown(
            '<div class="review-card" role="group" aria-label="Treatment settings">'
            '<h5>Treatment</h5>'
            f'<div class="review-line"><span class="review-label">Type</span>'
            f'<span class="review-value">{TREATMENT_LABELS.get(treatment, treatment)}</span></div>'
            f'<div class="review-line"><span class="review-label">Starts at</span>'
            f'<span class="review-value">Step {params["treatment_start"]}</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with pc3:
        st.markdown(
            '<div class="review-card" role="group" aria-label="Simulation settings">'
            '<h5>Simulation</h5>'
            f'<div class="review-line"><span class="review-label">Duration</span>'
            f'<span class="review-value">{params["max_steps"]} steps</span></div>'
            f'<div class="review-line"><span class="review-label">Grid</span>'
            f'<span class="review-value">{dim}\u00b3 ({dim**3:,} voxels)</span></div>'
            f'<div class="review-line"><span class="review-label">Seed</span>'
            f'<span class="review-value">{params["random_seed"]}</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Quick assessment of expected difficulty
    _assess_notes = []
    if treatment == "None":
        _assess_notes.append(":material/info: No treatment — tumor must be defeated by natural immunity alone")
    elif treatment == "ICI+TKI":
        _assess_notes.append(":material/security: Strongest treatment combination selected")
    if params["BMI"] >= 30:
        _assess_notes.append(":material/warning: High BMI weakens immune response")
    if params["treatment_start"] > 100 and treatment != "None":
        _assess_notes.append(":material/schedule: Late treatment start gives tumor time to grow")
    elif params["treatment_start"] <= 20 and treatment != "None":
        _assess_notes.append(":material/bolt: Early treatment — quick intervention")

    if _assess_notes:
        for note in _assess_notes:
            st.caption(note)
        st.markdown("")

    start_btn = st.button(":material/play_arrow: START SIMULATION",
                           type="primary", use_container_width=True)

    col_back, _ = st.columns([1, 3])
    with col_back:
        if st.button(":material/arrow_back: Change Settings", use_container_width=True):
            st.switch_page("pages/1_configure.py")

    if start_btn:
        import shutil
        can_run = True
        if not shutil.which("mpirun"):
            try:
                import mpi4py  # noqa: F401
            except ImportError:
                st.error("**Cannot start:** `mpirun` is not installed and `mpi4py` is unavailable. "
                         "Please install MPI to run simulations.")
                can_run = False
        if can_run:
            st.session_state["run_active"] = True
            st.rerun()

# =========================================================================
# PHASE 2: LIVE MONITORING
# =========================================================================

else:
    # ---- HEADER ----
    hud_header_html = (
        '<div class="hud-header" role="banner" aria-label="Simulation status">'
        '<span class="hud-title">'
        '<span class="hud-live-dot" aria-hidden="true"></span>SIMULATION RUNNING'
        '</span>'
        '<span style="color:#64748B;font-family:\'JetBrains Mono\',monospace;font-size:0.8rem">'
        f'{format_sex(params["sex"])} patient | '
        f'BMI {params["BMI"]:.0f} | '
        f'{TREATMENT_LABELS.get(params["treatment"], params["treatment"])}'
        '</span>'
        '</div>'
        '<div class="hud-scan-line"></div>'
    )
    st.markdown(hud_header_html, unsafe_allow_html=True)

    # ---- PROGRESS ----
    progress_bar = st.progress(0, text="Starting simulation...")

    # ---- CANCEL BUTTON ----
    # When clicked, Streamlit interrupts the running script and re-executes.
    # On re-entry, we detect the existing process via session_state and kill it.
    cancel_col, _ = st.columns([1, 5])
    with cancel_col:
        if st.button(
            ":material/stop: Cancel",
            type="secondary",
            use_container_width=True,
            help="Stop the simulation early. Results up to this point will be saved.",
        ):
            st.session_state["cancel_requested"] = True

    # ---- 3D CONTROLS & LAYOUT ----
    _CAMERA_PRESETS = {
        "Default": dict(eye=dict(x=1.5, y=1.5, z=1.5)),
        "Top-Down": dict(eye=dict(x=0, y=0, z=2.5), up=dict(x=0, y=1, z=0)),
        "Front": dict(eye=dict(x=0, y=2.5, z=0.3)),
        "Side": dict(eye=dict(x=2.5, y=0, z=0.3)),
    }
    # ==== LAYOUT ====
    # ROW 0: 3D view (65%) | Status panel (35%)
    r0_left, r0_right = st.columns([65, 35])
    with r0_left:
        env_3d_slot = st.empty()
        snap_label_slot = st.empty()
        # Cell color legend
        st.markdown(
            '<div class="cell-legend" role="group" aria-label="Cell type color legend">'
            '<div class="cell-legend-item"><div class="cell-legend-dot" style="background:#DC2626" aria-hidden="true"></div>Tumor</div>'
            '<div class="cell-legend-item"><div class="cell-legend-dot" style="background:#2563EB" aria-hidden="true"></div>Killer T-Cell</div>'
            '<div class="cell-legend-item"><div class="cell-legend-dot" style="background:#7C3AED" aria-hidden="true"></div>NK Cell</div>'
            '<div class="cell-legend-item"><div class="cell-legend-dot" style="background:#EA580C" aria-hidden="true"></div>M1 Macrophage</div>'
            '<div class="cell-legend-item"><div class="cell-legend-dot" style="background:#FB923C" aria-hidden="true"></div>M2 Macrophage</div>'
            '<div class="cell-legend-item"><div class="cell-legend-dot" style="background:#D946EF" aria-hidden="true"></div>Dendritic</div>'
            '<div class="cell-legend-item"><div class="cell-legend-dot" style="background:#06B6D4" aria-hidden="true"></div>Neutrophil</div>'
            '<div class="cell-legend-item"><div class="cell-legend-dot" style="background:#16A34A" aria-hidden="true"></div>CD4 T-Cell</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.caption("Drag to rotate, scroll to zoom.")
        with st.expander("View Controls", expanded=False):
            _ctrl_c1, _ctrl_c2, _ctrl_c3 = st.columns([2, 1, 2])
            with _ctrl_c1:
                _live_filter = st.selectbox("Show",
                    ["All Cells", "Tumor + Immune", "Immune Only"],
                    index=1, key="live_env_filter",
                    help="Which cell types to show in the 3D view")
            with _ctrl_c2:
                _live_marker_size = st.slider("Dot size", 1, 10, 3,
                    key="live_env_marker_size")
            with _ctrl_c3:
                _live_camera_name = st.selectbox("Camera angle",
                    list(_CAMERA_PRESETS.keys()),
                    index=0, key="live_env_camera")
    with r0_right:
        stats_slot = st.empty()
        status_msg_slot = st.empty()

    # Resolve filter
    if _live_filter == "All Cells":
        _live_vis_types = None
    elif _live_filter == "Tumor + Immune":
        _immune = frozenset(t for t in AgentType if t not in NON_IMMUNE)
        _live_vis_types = {int(AgentType.TUMOR_CELL)} | {int(t) for t in _immune}
    else:
        _immune = frozenset(t for t in AgentType if t not in NON_IMMUNE)
        _live_vis_types = {int(t) for t in _immune}

    _live_camera = _CAMERA_PRESETS[_live_camera_name]

    # ROW 1: Tumor chart | Immune vs Tumor chart
    r1_left, r1_right = st.columns(2)
    with r1_left:
        tumor_chart_slot = st.empty()
    with r1_right:
        immune_chart_slot = st.empty()

    # ROW 2: Glucose | Density map
    r2_left, r2_right = st.columns(2)
    with r2_left:
        glucose_chart_slot = st.empty()
    with r2_right:
        st.caption("Cell density from above — brighter areas have more cells.")
        density_slot = st.empty()

    # ROW 3: Log
    with st.expander("Technical Log", expanded=False, icon=":material/terminal:"):
        log_slot = st.empty()

    # Slot for post-simulation timeline
    timeline_container = st.container()

    # ---- LAUNCH PROCESS (or handle cancel of existing) ----
    # If a previous run's process is still alive and cancel was requested, kill it
    _prev_proc = st.session_state.get("_sim_process")
    if st.session_state.get("cancel_requested") and _prev_proc is not None:
        cancel_simulation(_prev_proc)
        _prev_ctx = st.session_state.get("_sim_ctx", {})
        st.session_state.pop("_sim_process", None)
        st.session_state.pop("_sim_ctx", None)
        st.session_state.pop("cancel_requested", None)
        # Finalize whatever we have
        meta = finalize_run(_prev_ctx, params, outcome="UNKNOWN")
        st.session_state["last_run_dir"] = _prev_ctx.get("run_dir")
        st.session_state["last_run_meta"] = meta
        st.session_state["run_active"] = False
        progress_bar.progress(1.0, text="Simulation cancelled by user.")
        st.toast("Simulation cancelled. Partial results saved.", icon="\u26d4")
        st.rerun()

    ctx = start_simulation(params, snapshot_interval=st.session_state.get("snapshot_interval", 0))
    proc = ctx["process"]
    # Store process in session_state so cancel-on-rerun can find it
    st.session_state["_sim_process"] = proc
    st.session_state["_sim_ctx"] = ctx
    snapshot_dir = snapshot_dir_for(ctx["run_dir"])
    treatment_start = params.get("treatment_start")

    # Accumulation buffers
    hist_steps, hist_tumor, hist_agents, hist_glucose, hist_immune = [], [], [], [], []

    last_rendered_step = -1
    detected_outcome = "UNKNOWN"
    last_progress = None
    prev_progress = None
    initial_tumor = None
    initial_agents = None
    peak_tumor = 0
    peak_step = 0
    log_lines = deque(maxlen=30)
    tick = 0
    last_chart_tick = -_CHART_UPDATE_INTERVAL

    # Early termination detection
    early_terminated = False
    termination_step = None
    _prev_step = -1
    _frozen_count = 0

    sim_start = time.time()

    cancelled = False

    try:
        while True:
            # Cancel is handled via Streamlit rerun (button click interrupts this loop).
            # This check handles the timeout case only.

            # Check for timeout
            if check_timeout(ctx):
                cancel_simulation(proc)
                cancelled = True
                progress_bar.progress(1.0, text="Simulation timed out (30 min limit).")
                st.warning("The simulation exceeded the maximum allowed time and was stopped.")
                break

            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if not line:
                continue

            line = line.rstrip()
            log_lines.append(line)

            if detected_outcome == "UNKNOWN":
                if "SURVIVAL" in line:
                    detected_outcome = "SURVIVAL"
                elif "PROGRESSION" in line:
                    detected_outcome = "PROGRESSION"

            prog = parse_progress_line(line)
            if not prog:
                continue

            prev_progress = last_progress
            last_progress = prog
            if initial_tumor is None:
                initial_tumor = prog["tumor"]
                initial_agents = prog["agents"]

            step = prog["step"]
            max_steps = prog["max_steps"]

            # ---- EARLY TERMINATION DETECTION ----
            if step == _prev_step:
                _frozen_count += 1
                if _frozen_count == 1:
                    early_terminated = True
                    termination_step = step
                    if hist_tumor and hist_tumor[-1] == 0:
                        detected_outcome = "SURVIVAL"
                    elif hist_tumor and hist_tumor[-1] >= _CRITICAL_MASS:
                        detected_outcome = "PROGRESSION"
                    reason = _termination_reason(hist_tumor, initial_tumor)
                    progress_bar.progress(1.0,
                        text=f"Finished at step {step}/{max_steps} \u2014 {reason}")
                    # Final chart render
                    fig_tumor = _hud_tumor_chart(hist_steps, hist_tumor,
                                                 treatment_start, termination_step)
                    tumor_chart_slot.plotly_chart(fig_tumor, use_container_width=True)
                    fig_immune = _hud_immune_chart(hist_steps, hist_tumor,
                                                   hist_immune, treatment_start)
                    immune_chart_slot.plotly_chart(fig_immune, use_container_width=True)
                    fig_gluc = _hud_glucose_chart(hist_steps, hist_glucose)
                    glucose_chart_slot.plotly_chart(fig_gluc, use_container_width=True)
                    log_slot.code("\n".join(log_lines), language=None)
                continue
            _prev_step = step
            _frozen_count = 0

            pct = step / max_steps
            elapsed = time.time() - sim_start
            eta = elapsed / max(1, step) * (max_steps - step) if step > 0 else 0

            if prog["tumor"] > peak_tumor:
                peak_tumor = prog["tumor"]
                peak_step = step

            est_immune = max(0, prog["agents"] - prog["tumor"])

            # Accumulate
            hist_steps.append(step)
            hist_tumor.append(prog["tumor"])
            hist_agents.append(prog["agents"])
            hist_glucose.append(prog["glucose"])
            hist_immune.append(est_immune)

            tick += 1
            tumor_delta = None
            if prev_progress:
                tumor_delta = prog["tumor"] - prev_progress["tumor"]

            # ---- PROGRESS BAR ----
            if treatment_start is not None and step < treatment_start:
                phase_text = "Observing tumor growth"
            elif treatment_start is not None and step == treatment_start:
                phase_text = "Treatment begins now"
            elif params["treatment"] == "None":
                phase_text = "No treatment — natural immunity"
            else:
                phase_text = f"{TREATMENT_LABELS.get(params['treatment'], 'Treatment')} active"

            progress_bar.progress(
                pct,
                text=(f"Step {step}/{max_steps}  \u2022  {phase_text}  \u2022  "
                      f"ETA {eta:.0f}s  \u2022  {elapsed:.0f}s elapsed"),
            )

            # ---- STATUS PANEL ----
            tumor_change = prog["tumor"] - (initial_tumor or prog["tumor"])
            tumor_pct = tumor_change / max(1, initial_tumor or 1) * 100
            trend_class = "bad" if tumor_change > 0 else ("good" if tumor_change < 0 else "neutral")
            itr = est_immune / max(1, prog["tumor"])
            if itr > 2:
                balance_label = "Immune winning"
                balance_class = "good"
            elif itr > 1:
                balance_label = "Balanced"
                balance_class = "neutral"
            else:
                balance_label = "Tumor winning"
                balance_class = "bad"
            throughput = step / max(1, elapsed)

            stats_html = (
                '<div class="hud-panel" role="status" aria-label="Simulation progress">'
                '<div class="hud-panel-title">PROGRESS</div>'
                + _hud_stat("STEP", f"{step} / {max_steps}", "neutral")
                + _hud_stat("TIME", f"{elapsed:.0f}s (ETA {eta:.0f}s)" if step > 0 else f"{elapsed:.0f}s", "neutral")
                + _hud_stat("PHASE", phase_text, "good" if treatment_start is not None and step >= treatment_start and params["treatment"] != "None" else "neutral")
                + _hud_stat("SPEED", f"{throughput:.1f} steps/sec", "neutral")
                + '</div>'
                '<div class="hud-panel" role="status" aria-label="Battle status">'
                '<div class="hud-panel-title">BATTLE STATUS</div>'
                + _hud_stat("TUMOR CELLS", f"{prog['tumor']:,}", "tumor", delta=tumor_delta)
                + _hud_stat("IMMUNE CELLS", f"{est_immune:,}", "immune")
                + _hud_stat("BALANCE", balance_label, balance_class)
                + _hud_stat("GLUCOSE", f"{prog['glucose']:.3f}", "glucose")
                + _hud_stat("TUMOR CHANGE", f"{tumor_pct:+.1f}% from start", trend_class)
                + '</div>'
            )
            stats_slot.markdown(stats_html, unsafe_allow_html=True)

            # ---- STATUS MESSAGE ----
            msg = _status_message(prog["tumor"], initial_tumor, est_immune,
                                  step, treatment_start)
            status_msg_slot.caption(f"_{msg}_")

            # ---- CHARTS (throttled) ----
            should_update_charts = (tick - last_chart_tick) >= _CHART_UPDATE_INTERVAL
            is_last_step = (step == max_steps)

            if should_update_charts or is_last_step:
                last_chart_tick = tick

                fig_tumor = _hud_tumor_chart(hist_steps, hist_tumor,
                                             treatment_start, termination_step)
                tumor_chart_slot.plotly_chart(fig_tumor, use_container_width=True)

                fig_immune = _hud_immune_chart(hist_steps, hist_tumor,
                                               hist_immune, treatment_start)
                immune_chart_slot.plotly_chart(fig_immune, use_container_width=True)

                fig_gluc = _hud_glucose_chart(hist_steps, hist_glucose)
                glucose_chart_slot.plotly_chart(fig_gluc, use_container_width=True)

            # ---- 3D + DENSITY MAP ----
            snap_path = snapshot_dir / f"step_{step:05d}.npz"
            if snap_path.exists() and step > last_rendered_step:
                last_rendered_step = step
                _render_snapshot(snap_path, env_3d_slot, None,
                                 visible_types=_live_vis_types,
                                 marker_size=_live_marker_size,
                                 camera=_live_camera)
                snap_label_slot.caption(f"Showing step {step} of {max_steps}")
                _render_density_map(snap_path, density_slot, None)

            # ---- LOG ----
            log_slot.code("\n".join(log_lines), language=None)

    except Exception as e:
        st.error(f"Simulation error: {e}")

    # Wait for process (stderr is merged into stdout via STDOUT redirect)
    returncode = proc.wait() if not cancelled else proc.poll() or 0

    # ---- POST-SIMULATION SNAPSHOT TIMELINE ----
    available_snaps = list_snapshot_steps(snapshot_dir)
    if len(available_snaps) > 1:
        with timeline_container:
            st.markdown("#### Browse the Simulation Timeline")
            st.caption("Drag the slider to see the 3D state at any recorded step.")
            sel = st.select_slider(
                "Step",
                options=available_snaps,
                value=available_snaps[-1],
                format_func=lambda s: f"Step {s}",
                label_visibility="collapsed",
            )
            snap_path = snapshot_dir / f"step_{sel:05d}.npz"
            _render_snapshot(snap_path, env_3d_slot, None,
                             visible_types=_live_vis_types,
                             marker_size=_live_marker_size,
                             camera=_live_camera)
            snap_label_slot.caption(f"Showing step {sel}")
            _render_density_map(snap_path, density_slot, None)

    # =====================================================================
    # PHASE 3: RESULTS
    # =====================================================================

    if returncode == 0 or cancelled:
        if not early_terminated:
            progress_bar.progress(1.0, text="Simulation complete!")

        final_snap = latest_snapshot(snapshot_dir)
        if final_snap is not None and len(available_snaps) <= 1:
            _render_snapshot(final_snap, env_3d_slot, None,
                             visible_types=_live_vis_types,
                             marker_size=_live_marker_size,
                             camera=_live_camera)
            _render_density_map(final_snap, density_slot, None)

        meta = finalize_run(ctx, params, outcome=detected_outcome)
        st.session_state["last_run_dir"] = ctx["run_dir"]
        st.session_state["last_run_meta"] = meta
        st.session_state["run_active"] = False
        st.session_state.pop("_sim_process", None)
        st.session_state.pop("_sim_ctx", None)
        st.session_state.pop("cancel_requested", None)
        outcome = meta["outcome"]
        elapsed_total = meta["elapsed_seconds"]

        # Completion notification
        if outcome == "SURVIVAL":
            st.toast("Simulation complete — Tumor eliminated!", icon="\u2705")
        elif outcome == "PROGRESSION":
            st.toast("Simulation complete — Tumor progressed.", icon="\u274c")
        else:
            st.toast("Simulation complete.", icon="\u2753")

        # ---- Outcome banner ----
        st.divider()
        st.markdown('<div style="text-align:center;padding:16px 0">', unsafe_allow_html=True)
        render_outcome_badge(outcome)
        if outcome == "SURVIVAL":
            st.markdown(
                '<p style="color:#059669;margin:8px 0 0;font-size:1.1rem">'
                'The immune system eliminated the tumor!</p>',
                unsafe_allow_html=True)
        elif outcome == "PROGRESSION":
            st.markdown(
                '<p style="color:#DC2626;margin:8px 0 0;font-size:1.1rem">'
                'The tumor grew beyond critical mass.</p>',
                unsafe_allow_html=True)
        st.markdown(
            f'<p style="color:#64748B;margin:4px 0 0">'
            f'Completed in <strong>{elapsed_total:.1f}s</strong> '
            f'({meta["max_steps"]} steps)</p>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # ---- Full results from CSV ----
        df = load_run_csv(ctx["run_dir"])

        if df is not None:
            st.subheader("Detailed Results")

            if "tumor_cells" in df.columns:
                init_t = int(df["tumor_cells"].iloc[0])
                final_t = int(df["tumor_cells"].iloc[-1])
                peak_t = int(df["tumor_cells"].max())
                pk_step = int(df.loc[df["tumor_cells"].idxmax(), "step"])
                net = final_t - init_t
                net_pct = net / max(1, init_t) * 100

                rc1, rc2, rc3, rc4 = st.columns(4)
                rc1.metric("Started With", f"{init_t:,} tumor cells")
                rc2.metric("Peak Size", f"{peak_t:,} cells", delta=f"at step {pk_step}")
                rc3.metric("Ended With", f"{final_t:,} cells")
                rc4.metric("Net Change", f"{net:+,} cells", delta=f"{net_pct:+.1f}%",
                           delta_color="inverse")

                # Plain-language interpretation
                if final_t == 0:
                    st.success("The immune system completely eliminated the tumor.")
                elif net_pct > 100:
                    st.error(f"The tumor more than doubled (+{net_pct:.0f}%). Treatment was insufficient.")
                elif net_pct < -50:
                    st.success(f"The tumor shrank by {abs(net_pct):.0f}% — treatment was very effective.")

            tab_pop, tab_tumor, tab_kills, tab_gluc, tab_immune = st.tabs([
                ":material/trending_up: Tumor Growth",
                ":material/groups: All Cell Types",
                ":material/swords: Immune Kills",
                ":material/water_drop: Glucose",
                ":material/shield: Kill Breakdown",
            ])

            with tab_pop:
                fig = tumor_growth(df, treatment_start)
                st.plotly_chart(fig, use_container_width=True)

            with tab_tumor:
                fig = population_dynamics(df)
                st.plotly_chart(fig, use_container_width=True)

            with tab_kills:
                fig = kill_counts(df)
                st.plotly_chart(fig, use_container_width=True)
                existing_kills = [c for c in KILL_COLS if c in df.columns]
                if existing_kills:
                    kcols = st.columns(len(existing_kills))
                    for kc, kn in zip(kcols, existing_kills):
                        kc.metric(format_column_name(kn), f"{int(df[kn].iloc[-1]):,}")

            with tab_gluc:
                fig = glucose_dashboard(df)
                st.plotly_chart(fig, use_container_width=True)

            with tab_immune:
                immune_kill_cols = [c for c in KILL_COLS if c in df.columns and c != "apoptosis_count"]
                if immune_kill_cols:
                    fig = immune_effectiveness_pie(df)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No immune kill data recorded for this run.")

            csv_data = df.to_csv(index=False)
            st.download_button(":material/download: Download Data (CSV)", data=csv_data,
                               file_name=f"sim_{meta['run_id']}.csv", mime="text/csv")

        # What to try next
        st.divider()
        st.subheader("What Now?")
        nav1, nav2, nav3, nav4 = st.columns(4)
        with nav1:
            if st.button(":material/show_chart: Full Results",
                         type="primary", use_container_width=True):
                st.switch_page("pages/3_results.py")
        with nav2:
            if st.button(":material/view_in_ar: Explore in 3D", use_container_width=True):
                st.switch_page("pages/5_environment.py")
        with nav3:
            if st.button(":material/replay: Run Again", use_container_width=True,
                         help="Re-run with the same settings"):
                st.session_state["run_active"] = False
                st.rerun()
        with nav4:
            if st.button(":material/settings: Change Settings", use_container_width=True,
                         help="Try a different treatment or patient"):
                st.switch_page("pages/1_configure.py")

    else:
        progress_bar.progress(1.0, text="Simulation failed")
        st.session_state["run_active"] = False
        st.session_state.pop("_sim_process", None)
        st.session_state.pop("_sim_ctx", None)
        st.session_state.pop("cancel_requested", None)
        st.error(f"The simulation stopped with an error (code {returncode}). "
                 "Check the log above for error details, or try different settings.")
        if log_lines:
            with st.expander("Error Details", expanded=True, icon=":material/error:"):
                st.code("\n".join(log_lines), language=None)

        c1, c2 = st.columns(2)
        with c1:
            if st.button(":material/settings: Change Settings", use_container_width=True):
                st.switch_page("pages/1_configure.py")
        with c2:
            if st.button(":material/replay: Try Again", use_container_width=True):
                st.session_state["run_active"] = True
                st.rerun()

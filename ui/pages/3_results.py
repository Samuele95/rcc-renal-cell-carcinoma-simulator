"""Results visualization page — understand what happened in your simulation."""

import streamlit as st

from ui.lib.state import list_runs, load_run_csv, read_meta
from ui.lib.charts import (
    population_dynamics, tumor_growth, kill_counts, kill_rate,
    glucose_dashboard, glucose_analysis_dashboard,
    immune_effectiveness_pie, NON_CELL_COLS, KILL_COLS,
)
from ui.lib.formatting import (
    render_outcome_badge, format_sex, format_column_name,
    format_kill_column_name, treatment_badge_html, TREATMENT_LABELS,
)

# Critical mass threshold — kept in sync with engine (rcc_model.py:56)
_CRITICAL_MASS = 2000

st.title("Simulation Results")
st.caption("Explore what happened during a simulation run.")

# ---------------------------------------------------------------------------
# Run selector
# ---------------------------------------------------------------------------

runs = list_runs()
if not runs:
    st.markdown("""
    **No results yet.** Run your first simulation to see detailed charts and analysis here.

    Results will show:
    - How the tumor grew or shrank over time
    - Which immune cells were most effective
    - Glucose (energy) levels in the tissue
    - A breakdown of all immune kills
    """)
    if st.button(":material/play_arrow: Set Up Your First Simulation", type="primary"):
        st.switch_page("pages/1_configure.py")
    st.stop()

# Default to last run if available
default_idx = 0
last_dir = st.session_state.get("last_run_dir")
if last_dir:
    for i, r in enumerate(runs):
        if r.get("run_dir") == last_dir:
            default_idx = i
            break

def _format_run_label(i):
    r = runs[i]
    outcome = r.get("outcome", "?")
    icon = "\u2705" if outcome == "SURVIVAL" else ("\u274c" if outcome == "PROGRESSION" else "\u2753")
    sex = format_sex(r.get("sex", "?"))
    treatment = TREATMENT_LABELS.get(r.get("treatment", "?"), r.get("treatment", "?"))
    return f"{icon}  {treatment} | {sex}, BMI {r.get('BMI', '?')} | {outcome}"


selected_idx = st.selectbox(
    "Select a simulation run", range(len(runs)), index=default_idx,
    format_func=_format_run_label, key="results_run_select",
)

selected_run = runs[selected_idx]
run_dir = selected_run["run_dir"]

# Load data
df = load_run_csv(run_dir)
if df is None:
    st.error("Could not load data for this run. The simulation log file may be missing.")
    st.stop()

# ---------------------------------------------------------------------------
# Run summary header
# ---------------------------------------------------------------------------

outcome = selected_run.get("outcome", "?")

header_cols = st.columns([1, 4])
with header_cols[0]:
    render_outcome_badge(outcome)
with header_cols[1]:
    treatment = TREATMENT_LABELS.get(selected_run.get("treatment", "?"),
                                       selected_run.get("treatment", "?"))
    sex_display = format_sex(selected_run.get("sex", "?"))
    bmi = selected_run.get("BMI", "?")
    elapsed = selected_run.get("elapsed_seconds", 0)
    st.markdown(
        f"**Patient:** {sex_display}, BMI {bmi} &nbsp;&bull;&nbsp; "
        f"**Treatment:** {treatment} &nbsp;&bull;&nbsp; "
        f"**Duration:** {elapsed:.1f}s &nbsp;&bull;&nbsp; "
        f"**Steps:** {len(df)}"
    )

st.divider()

# ---------------------------------------------------------------------------
# Quick summary metrics
# ---------------------------------------------------------------------------

if "tumor_cells" in df.columns:
    peak = int(df["tumor_cells"].max())
    peak_step = int(df.loc[df["tumor_cells"].idxmax(), "step"])
    final_tumor = int(df["tumor_cells"].iloc[-1])
    initial_tumor = int(df["tumor_cells"].iloc[0])
    change = final_tumor - initial_tumor
    change_pct = (change / max(1, initial_tumor)) * 100

    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Started With", f"{initial_tumor:,} tumor cells")
    sc2.metric("Peak Size", f"{peak:,} cells", delta=f"at step {peak_step}")
    sc3.metric("Ended With", f"{final_tumor:,} cells")
    sc4.metric("Net Change", f"{change:+,} cells", delta=f"{change_pct:+.1f}%",
               delta_color="inverse")

    # Plain-language interpretation
    if final_tumor == 0:
        st.success("The immune system completely eliminated the tumor.")
    elif change_pct < -50:
        st.success(f"The tumor shrank by {abs(change_pct):.0f}% — treatment was very effective.")
    elif change_pct < -20:
        st.success(f"The tumor shrank by {abs(change_pct):.0f}% — treatment appears effective.")
    elif change_pct > 100:
        st.error(f"The tumor more than doubled in size (+{change_pct:.0f}%). Treatment was insufficient.")
    elif change_pct > 50:
        st.warning(f"The tumor grew by {change_pct:.0f}% — significant progression.")

    # Visual story timeline
    treatment_start = selected_run.get("treatment_start")
    total_steps = len(df)
    story_parts = []
    story_parts.append(f"The simulation started with **{initial_tumor:,} tumor cells**.")
    if treatment_start is not None and treatment_start < total_steps and selected_run.get("treatment") != "None":
        _trt_label = TREATMENT_LABELS.get(selected_run.get("treatment", "?"), "treatment")
        pre_tumor = df.loc[df["step"] <= treatment_start, "tumor_cells"]
        if len(pre_tumor) > 1:
            pre_change = int(pre_tumor.iloc[-1] - pre_tumor.iloc[0])
            if pre_change > 0:
                story_parts.append(
                    f"During the first {treatment_start} steps (before treatment), "
                    f"the tumor grew by **{pre_change:,} cells**.")
            else:
                story_parts.append(
                    f"Before treatment, the tumor {'stayed stable' if pre_change == 0 else 'shrank slightly'}.")
        story_parts.append(f"**{_trt_label}** began at step {treatment_start}.")
    if peak > initial_tumor:
        story_parts.append(f"The tumor peaked at **{peak:,} cells** (step {peak_step}).")
    if final_tumor == 0:
        # Find when it hit 0
        zero_steps = df.loc[df["tumor_cells"] == 0, "step"]
        if len(zero_steps) > 0:
            story_parts.append(f"All tumor cells were eliminated by **step {int(zero_steps.iloc[0])}**.")
    elif final_tumor >= _CRITICAL_MASS:
        story_parts.append(f"The tumor reached critical mass (**{final_tumor:,} cells**) and was not controlled.")
    else:
        story_parts.append(f"The simulation ended with **{final_tumor:,} tumor cells** remaining.")
        # Trend analysis for UNKNOWN outcomes
        if outcome == "UNKNOWN" or (outcome != "SURVIVAL" and outcome != "PROGRESSION"):
            # Look at the last 20% of steps to determine trend
            tail_frac = max(1, len(df) // 5)
            tail = df["tumor_cells"].iloc[-tail_frac:]
            if len(tail) > 1:
                trend_slope = tail.iloc[-1] - tail.iloc[0]
                if trend_slope > 0:
                    story_parts.append(
                        f"**Trend:** The tumor was still growing in the last {tail_frac} steps "
                        f"(+{int(trend_slope):,} cells). A longer simulation may lead to progression."
                    )
                elif trend_slope < 0:
                    story_parts.append(
                        f"**Trend:** The tumor was shrinking in the last {tail_frac} steps "
                        f"({int(trend_slope):,} cells). A longer simulation may lead to survival."
                    )
                else:
                    story_parts.append(
                        "**Trend:** The tumor was stable in the final steps — a dynamic equilibrium."
                    )

    with st.container(border=True):
        st.markdown("**What happened:**  \n" + "  \n".join(story_parts))

    st.caption(
        ":material/casino: **Note:** This is a stochastic simulation — results vary between runs "
        "even with identical settings. Change the random seed and re-run to see how "
        "variability affects the outcome."
    )

    st.divider()

# ---------------------------------------------------------------------------
# Chart tabs
# ---------------------------------------------------------------------------

tab_tumor, tab_pop, tab_kills, tab_killrate, tab_glucose, tab_immune = st.tabs([
    ":material/trending_up: Tumor Growth",
    ":material/groups: All Cell Types",
    ":material/swords: Immune Kills",
    ":material/speed: Kill Rate",
    ":material/water_drop: Glucose (Energy)",
    ":material/shield: Kill Breakdown",
])

# --- Tumor Growth (first — most important) ---
with tab_tumor:
    st.caption("How did the tumor grow or shrink over time? The treatment start is marked if applicable.")
    treatment_start = selected_run.get("treatment_start")
    if treatment_start is None:
        try:
            meta = read_meta(run_dir)
            treatment_start = meta.get("treatment_start")
        except Exception:
            pass
    fig = tumor_growth(df, treatment_start)
    st.plotly_chart(fig, use_container_width=True)

    # Phase analysis
    if treatment_start is not None and "tumor_cells" in df.columns and treatment_start < df["step"].max():
        pre = df[df["step"] <= treatment_start]
        post = df[df["step"] > treatment_start]
        if len(pre) > 1 and len(post) > 1:
            st.subheader("Before vs After Treatment")
            pa1, pa2 = st.columns(2)
            with pa1:
                pre_change = int(pre["tumor_cells"].iloc[-1] - pre["tumor_cells"].iloc[0])
                pre_label = "grew" if pre_change > 0 else "shrank"
                st.metric("Before Treatment", f"{pre_change:+,} cells",
                          delta=f"tumor {pre_label} over {len(pre)} steps")
            with pa2:
                post_change = int(post["tumor_cells"].iloc[-1] - post["tumor_cells"].iloc[0])
                post_label = "grew" if post_change > 0 else "shrank"
                st.metric("After Treatment", f"{post_change:+,} cells",
                          delta=f"tumor {post_label} over {len(post)} steps",
                          delta_color="inverse" if post_change > 0 else "normal")

# --- All Cell Types ---
with tab_pop:
    st.caption("Track how every cell type changed over the simulation. "
               "Use the filter to focus on specific types.")
    cell_cols = [c for c in df.columns if c not in NON_CELL_COLS]

    opt1, opt2 = st.columns([3, 1])
    with opt1:
        selected_types = st.multiselect(
            "Show cell types",
            options=cell_cols,
            default=cell_cols,
            format_func=format_column_name,
            key="pop_filter",
        )
    with opt2:
        log_scale = st.toggle("Log scale", value=False, key="pop_log",
                               help="Useful to see small populations alongside large ones")

    fig = population_dynamics(df, selected_types if selected_types else None, log_scale=log_scale)
    st.plotly_chart(fig, use_container_width=True)

# --- Kill Counts ---
with tab_kills:
    st.caption("How many tumor cells did each immune cell type kill? "
               "Higher counts mean that cell type was more active in fighting the tumor.")
    stacked = st.toggle("Show stacked (total immune activity)", value=False, key="kill_stacked")
    fig = kill_counts(df, stacked=stacked)
    st.plotly_chart(fig, use_container_width=True)

    # Final kill totals
    existing_kills = [c for c in KILL_COLS if c in df.columns]
    if existing_kills:
        st.markdown("**Who killed the most tumor cells?**")
        # Sort by kill count descending
        kill_pairs = [(c, int(df[c].iloc[-1])) for c in existing_kills]
        kill_pairs.sort(key=lambda x: -x[1])
        kill_cols_ui = st.columns(len(kill_pairs))
        for j, (col_name, final_val) in enumerate(kill_pairs):
            with kill_cols_ui[j]:
                label = format_kill_column_name(col_name)
                if j == 0 and final_val > 0:
                    st.metric(f":material/star: {label}", f"{final_val:,}")
                else:
                    st.metric(label, f"{final_val:,}")

# --- Kill Rate ---
with tab_killrate:
    st.caption("How fast were immune cells killing tumor cells at each step? "
               "Peaks show when the immune response was most intense.")
    fig = kill_rate(df)
    st.plotly_chart(fig, use_container_width=True)

# --- Glucose ---
with tab_glucose:
    st.caption("Glucose is the energy source for all cells. Tumor cells consume it heavily "
               "(the 'Warburg effect'). When glucose drops, immune cells become less effective.")
    
    # Basic glucose metrics
    st.subheader("Basic Glucose Metrics")
    fig = glucose_dashboard(df)
    st.plotly_chart(fig, use_container_width=True)
    
    # Enhanced glucose analysis (Professor's requirements)
    st.subheader("Advanced Glucose Analysis")
    st.caption("Enhanced analysis for glucose presence verification, concentration gradients, "
               "and spatial distribution patterns as requested by the professor.")
    fig_analysis = glucose_analysis_dashboard(df)
    st.plotly_chart(fig_analysis, use_container_width=True)
    
    # Summary metrics for latest step
    if len(df) > 0:
        latest = df.iloc[-1]
        st.subheader("Latest Analysis Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            coverage = latest.get('glucose_coverage_percent', 0)
            st.metric("Glucose Coverage", f"{coverage:.1f}%", 
                     help="Percentage of tissue with detectable glucose")
        
        with col2:
            confidence = latest.get('glucose_detection_confidence', 0)
            st.metric("Detection Confidence", f"{confidence:.2f}", 
                     help="Confidence in glucose presence detection (0-1)")
        
        with col3:
            gradient_mag = latest.get('glucose_gradient_mean_magnitude', 0)
            st.metric("Mean Gradient", f"{gradient_mag:.3f}", 
                     help="Average concentration gradient magnitude")
        
        with col4:
            hotspots = latest.get('glucose_hotspots_count', 0)
            st.metric("Hotspots", f"{int(hotspots)}", 
                     help="Number of high-concentration regions")
    
    # Link to advanced glucose visualization
    if st.button("🔬 Explore Glucose Field in 3D", type="primary", use_container_width=True):
        st.info("Switch to the Glucose Field page to see detailed 3D visualizations of energy distribution in the tissue.")
        st.switch_page("pages/7_glucose.py")

# --- Immune Effectiveness ---
with tab_immune:
    st.caption("Which immune cell types contributed the most to tumor killing? "
               "This shows the breakdown of all immune kills by cell type.")
    immune_kill_cols = [c for c in KILL_COLS if c in df.columns and c != "apoptosis_count"]
    if immune_kill_cols:
        fig = immune_effectiveness_pie(df)
        c_pie, c_table = st.columns([1, 1])
        with c_pie:
            st.plotly_chart(fig, use_container_width=True)
        with c_table:
            st.markdown("**Kill breakdown by cell type:**")
            kill_finals = {c: int(df[c].iloc[-1]) for c in immune_kill_cols}
            total_kills = sum(kill_finals.values())
            kill_data = [
                {
                    "Cell Type": format_kill_column_name(c),
                    "Kills": val,
                    "Share": f"{val / max(1, total_kills) * 100:.1f}%",
                }
                for c, val in kill_finals.items()
            ]
            import pandas as pd
            st.dataframe(pd.DataFrame(kill_data), use_container_width=True, hide_index=True)
            st.metric("Total Immune Kills", f"{total_kills:,}")
    else:
        st.info("No immune kill data was recorded for this run.")

# --- What to try next ---
st.divider()
st.subheader("What to Try Next")

_current_treatment = selected_run.get("treatment", "None")
_suggestions = []

if outcome == "PROGRESSION":
    if _current_treatment == "None":
        _suggestions.append(("Try Immunotherapy (ICI)", "The tumor grew without treatment. ICI can boost the immune system's ability to fight back."))
        _suggestions.append(("Try Combination (ICI+TKI)", "The strongest treatment option — attacks tumor from both sides."))
    elif _current_treatment == "ICI":
        _suggestions.append(("Try Combination (ICI+TKI)", "Immunotherapy alone wasn't enough. Adding TKI cuts off the tumor's blood supply."))
        _suggestions.append(("Try Earlier Treatment", "Starting treatment sooner gives the immune system a head start."))
    elif _current_treatment == "TKI":
        _suggestions.append(("Try Combination (ICI+TKI)", "TKI alone wasn't enough. Adding ICI boosts the immune attack."))
    elif _current_treatment == "ICI+TKI":
        _suggestions.append(("Try Earlier Treatment", "Even combination therapy can fail if the tumor grows too large before treatment starts."))
        _suggestions.append(("Try a Different Patient Profile", "BMI and sex affect immune response. Try a different patient."))
elif outcome == "SURVIVAL":
    if _current_treatment != "None":
        _suggestions.append(("Try Without Treatment", "Would this patient's immune system have won on its own?"))
    if _current_treatment == "ICI+TKI":
        _suggestions.append(("Try ICI Only", "Was immunotherapy alone sufficient? Simpler treatments are preferred when effective."))
    _suggestions.append(("Change the Random Seed", "Run the same scenario again to see if the outcome is consistent."))
else:
    _suggestions.append(("Run a Longer Simulation", "The outcome may not be clear yet. Try more steps."))
    _suggestions.append(("Try Combination (ICI+TKI)", "The strongest treatment option may produce a clearer result."))

_SUGGESTION_OVERRIDES = {
    "Try Immunotherapy (ICI)": {"treatment": "ICI"},
    "Try Combination (ICI+TKI)": {"treatment": "ICI+TKI"},
    "Try Earlier Treatment": lambda p: {"treatment_start": max(0, p.get("treatment_start", 50) - 30)},
    "Try Without Treatment": {"treatment": "None"},
    "Try ICI Only": {"treatment": "ICI"},
    "Try a Different Patient Profile": {},
    "Change the Random Seed": lambda p: {"random_seed": p.get("random_seed", 1) + 1},
    "Run a Longer Simulation": lambda p: {"max_steps": p.get("max_steps", 200) + 100},
}

sc_cols = st.columns(len(_suggestions))
for i, (title, desc) in enumerate(_suggestions):
    with sc_cols[i]:
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(desc)
        if st.button(f":material/settings: Set Up", key=f"suggest_{i}", use_container_width=True):
            # Pre-load suggested changes if available
            overrides = _SUGGESTION_OVERRIDES.get(title, {})
            if callable(overrides):
                overrides = overrides(st.session_state.get("params", {}))
            if overrides and "params" in st.session_state:
                st.session_state["params"].update(overrides)
                st.session_state["preset_selector"] = "Custom"
            st.switch_page("pages/1_configure.py")

# --- Navigation and Export ---
st.divider()
st.subheader("Explore Further")

nav_cols = st.columns(4)
with nav_cols[0]:
    if st.button(":material/water_drop: Glucose Field 3D", use_container_width=True, type="primary"):
        st.switch_page("pages/7_glucose.py")
with nav_cols[1]:
    if st.button(":material/view_in_ar: 3D Environment", use_container_width=True):
        st.switch_page("pages/5_environment.py")
with nav_cols[2]:
    if st.button(":material/compare: Compare Runs", use_container_width=True):
        st.switch_page("pages/4_history.py")
with nav_cols[3]:
    csv_data = df.to_csv(index=False)
    st.download_button(
        ":material/download: Export Data",
        data=csv_data,
        file_name=f"simulation_data_{selected_idx}.csv",
        mime="text/csv",
        use_container_width=True
    )

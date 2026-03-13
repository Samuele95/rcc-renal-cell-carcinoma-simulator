"""Interactive 3D Environment — explore the tumor microenvironment."""

from pathlib import Path

import numpy as np
import streamlit as st

from ui.lib.charts import AgentType, AGENT_TYPE_VIS, _DEFAULT_VIS, environment_3d, spatial_density_map, NON_IMMUNE, IMMUNE_TYPES
from ui.lib.state import load_snapshot, find_snapshot_runs, list_snapshot_steps, read_meta
from ui.lib.formatting import TREATMENT_LABELS

st.title("🔬 3D Environment Explorer")
st.caption("Explore the tumor microenvironment in 3D space. Watch how tumor cells (red) and immune cells (blue/green) "
           "interact in the simulated tissue. Each dot represents a single cell in the battle.")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Friendly names for cell types
CELL_TYPE_NAMES = {
    AgentType.TUMOR_CELL: "Tumor Cell",
    AgentType.CD8_CYTOTOXIC_T_CELL: "Killer T-Cell (CD8)",
    AgentType.CD8_NAIVE_T_CELL: "Naive CD8 T-Cell",
    AgentType.CD4_NAIVE_T_CELL: "Naive CD4 T-Cell",
    AgentType.CD4_HELPER1_T_CELL: "Helper T-Cell (Th1)",
    AgentType.CD4_HELPER2_T_CELL: "Helper T-Cell (Th2)",
    AgentType.REGULATORY_T_CELL: "Regulatory T-Cell (Treg)",
    AgentType.DENDRITIC_CELL: "Dendritic Cell",
    AgentType.PLASMACITOID_DC: "Plasmacytoid DC",
    AgentType.MACROPHAGE_M1: "Macrophage (M1, anti-tumor)",
    AgentType.MACROPHAGE_M2: "Macrophage (M2, pro-tumor)",
    AgentType.NATURAL_KILLER: "Natural Killer Cell",
    AgentType.MAST_CELL: "Mast Cell",
    AgentType.NEUTROPHIL: "Neutrophil",
    AgentType.ADIPOCYTE: "Fat Cell",
    AgentType.BLOOD: "Blood Vessel",
    AgentType.SEX_HORMONE: "Sex Hormone",
    AgentType.CYTOKINE: "Cytokine Signal",
}

DEFAULT_HIDDEN = {AgentType.SEX_HORMONE, AgentType.CYTOKINE}


@st.cache_data(show_spinner=False)
def _cached_load_snapshot(path: str) -> dict:
    return load_snapshot(path)


# ---------------------------------------------------------------------------
# Run selection
# ---------------------------------------------------------------------------

runs = find_snapshot_runs()

if not runs:
    st.markdown("""
    **No 3D snapshots yet.** When you run a simulation, the 3D state of the tissue is saved
    automatically every few steps. You can then explore the tumor and immune cells in 3D here.

    Each colored dot represents a cell — red for tumor, blue/purple/green for different immune cells.
    """)
    if st.button(":material/play_arrow: Set Up Your First Simulation", type="primary"):
        st.switch_page("pages/1_configure.py")
    st.stop()

run_labels = {}
for r in runs:
    outcome = r.get("outcome", "?")
    treatment = TREATMENT_LABELS.get(r.get("treatment", "?"), r.get("treatment", "?"))
    icon = "\u2705" if outcome == "SURVIVAL" else ("\u274c" if outcome == "PROGRESSION" else "\u2753")
    run_labels[r["run_id"]] = f"{icon} {treatment} — {outcome}"

selected_id = st.selectbox("Select a simulation run", options=list(run_labels.keys()),
                           format_func=lambda x: run_labels[x])

selected_run = next(r for r in runs if r["run_id"] == selected_id)
snapshot_dir = selected_run["snapshot_dir"]
steps = list_snapshot_steps(snapshot_dir)

if not steps:
    st.warning("No snapshot files found for this run.")
    st.stop()

# ---------------------------------------------------------------------------
# Step navigation
# ---------------------------------------------------------------------------

# Determine treatment start for phase labels
_treatment_start = None
try:
    _meta = read_meta(Path(snapshot_dir).parent)
    _treatment_start = _meta.get("treatment_start")
except Exception:
    pass

def _step_label(s):
    label = f"Step {s}"
    if _treatment_start is not None:
        if s < _treatment_start:
            label += " (before treatment)"
        elif s == _treatment_start:
            label += " (treatment starts)"
        else:
            label += " (during treatment)"
    return label

st.markdown("**Navigate through time:**")

# Determine current step index
_cur_step = st.session_state.get("env_step", steps[-1])
if _cur_step not in steps:
    _cur_step = steps[-1]
_cur_idx = steps.index(_cur_step)

def _go_prev():
    idx = steps.index(st.session_state["env_step"])
    if idx > 0:
        st.session_state["env_step"] = steps[idx - 1]

def _go_next():
    idx = steps.index(st.session_state["env_step"])
    if idx < len(steps) - 1:
        st.session_state["env_step"] = steps[idx + 1]

nav_cols = st.columns([1, 6, 1])

with nav_cols[0]:
    st.button(":material/skip_previous:", disabled=_cur_idx == 0, key="env_prev",
              use_container_width=True, help="Go to previous snapshot",
              on_click=_go_prev)

with nav_cols[1]:
    selected_step = st.select_slider(
        "Step", options=steps, value=steps[-1], key="env_step",
        label_visibility="collapsed",
        format_func=_step_label,
    )

with nav_cols[2]:
    st.button(":material/skip_next:", disabled=_cur_idx >= len(steps) - 1, key="env_next",
              use_container_width=True, help="Go to next snapshot",
              on_click=_go_next)

# Show current phase
if _treatment_start is not None:
    if selected_step < _treatment_start:
        st.caption(f"Pre-treatment phase — treatment starts at step {_treatment_start}")
    elif selected_step == _treatment_start:
        st.caption("Treatment begins at this step")
    else:
        st.caption(f"Treatment active (started at step {_treatment_start})")

# Load snapshot
snapshot_path = str(Path(snapshot_dir) / f"step_{selected_step:05d}.npz")
snap = _cached_load_snapshot(snapshot_path)
agents = snap["agents"]
glucose = snap["glucose"]
grid_dims = snap["grid_dims"]

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------

with st.sidebar:
    st.subheader("Display Options")

    dark_mode = st.toggle("Dark mode", value=True, key="env_dark_mode",
                          help="Dark background for better contrast")

    st.divider()

    # Quick filter presets
    st.markdown("**Show which cells?**")
    preset_filter = st.radio(
        "Cell filter", ["All Cells", "Tumor + Immune", "Immune Only", "Custom"],
        key="env_filter_preset", horizontal=True, label_visibility="collapsed",
    )

    all_type_ids = sorted(AGENT_TYPE_VIS.keys())

    if preset_filter == "All Cells":
        default_visible = [tid for tid in all_type_ids if tid not in DEFAULT_HIDDEN]
    elif preset_filter == "Tumor + Immune":
        default_visible = [AgentType.TUMOR_CELL] + [tid for tid in all_type_ids if tid in IMMUNE_TYPES]
    elif preset_filter == "Immune Only":
        default_visible = [tid for tid in all_type_ids if tid in IMMUNE_TYPES]
    else:
        default_visible = [tid for tid in all_type_ids if tid not in DEFAULT_HIDDEN]

    visible_types = st.multiselect(
        "Visible cell types",
        options=all_type_ids,
        default=default_visible,
        format_func=lambda tid: CELL_TYPE_NAMES.get(tid, AGENT_TYPE_VIS[tid].name),
        key="env_visible_types",
    )

    marker_size = st.slider("Dot size", min_value=1, max_value=10, value=3,
                             help="Make cells bigger or smaller in the 3D view")

    st.divider()

    st.markdown("**Camera angle**")
    camera_preset = st.radio(
        "Camera", ["Default", "Top-Down", "Front", "Side"],
        key="env_camera", horizontal=True, label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Glucose cross-sections**")
    st.caption("Show how glucose is distributed inside the tissue.")

    w, h, d = grid_dims
    glucose_slices = {}

    if st.checkbox("X slice", value=False):
        glucose_slices["x"] = st.slider("X position", 0, w - 1, w // 2, key="gx")
    if st.checkbox("Y slice", value=False):
        glucose_slices["y"] = st.slider("Y position", 0, h - 1, h // 2, key="gy")
    if st.checkbox("Z slice", value=False):
        glucose_slices["z"] = st.slider("Z position", 0, d - 1, d // 2, key="gz")

# ---------------------------------------------------------------------------
# Metrics row
# ---------------------------------------------------------------------------

n_agents = agents.shape[0]
if n_agents > 0:
    bin_counts = np.bincount(agents[:, 3], minlength=len(AgentType))
    counts_by_type = {i: int(c) for i, c in enumerate(bin_counts) if c > 0}
    n_tumor = int(bin_counts[AgentType.TUMOR_CELL])
    n_immune = sum(int(bin_counts[t]) for t in IMMUNE_TYPES)
else:
    counts_by_type = {}
    n_tumor = 0
    n_immune = 0
mean_gluc = float(np.mean(glucose))

itr = n_immune / max(1, n_tumor)
if itr > 2:
    balance = "Immune winning"
elif itr > 1:
    balance = "Balanced"
elif n_tumor == 0:
    balance = "No tumor"
else:
    balance = "Tumor winning"

mc1, mc2, mc3, mc4, mc5 = st.columns(5)
mc1.metric("Snapshot", f"Step {selected_step} of {steps[-1]}")
mc2.metric("Tumor Cells", f"{n_tumor:,}")
mc3.metric("Immune Cells", f"{n_immune:,}")
mc4.metric("Battle Status", balance)
mc5.metric("Avg. Glucose", f"{mean_gluc:.3f}")

# Quick interpretation
if n_tumor == 0:
    st.success("No tumor cells in this snapshot — the immune system has cleared the cancer.")
elif balance == "Immune winning":
    st.info(f"Immune cells outnumber tumor cells {itr:.1f}:1 — the immune system has the advantage.")
elif balance == "Tumor winning":
    st.warning(f"Tumor cells outnumber immune cells — the cancer is gaining ground.")

# ---------------------------------------------------------------------------
# 3D chart
# ---------------------------------------------------------------------------

camera_settings = {
    "Default": dict(eye=dict(x=1.5, y=1.5, z=1.5)),
    "Top-Down": dict(eye=dict(x=0, y=0, z=2.5), up=dict(x=0, y=1, z=0)),
    "Front": dict(eye=dict(x=0, y=2.5, z=0.3)),
    "Side": dict(eye=dict(x=2.5, y=0, z=0.3)),
}

tab_3d, tab_density, tab_compare = st.tabs([
    ":material/view_in_ar: 3D View",
    ":material/map: Top-Down Density",
    ":material/compare: Compare Snapshots",
])

with tab_3d:
    fig = environment_3d(
        agents=agents,
        glucose=glucose,
        grid_dims=grid_dims,
        visible_types=set(visible_types),
        marker_size=marker_size,
        glucose_slices=glucose_slices if glucose_slices else None,
        dark_mode=dark_mode,
    )
    fig.update_layout(scene_camera=camera_settings.get(camera_preset, {}))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Drag to rotate, scroll to zoom, right-click to pan. "
               "Red mass = tumor. Colored dots = immune cells.")
    with st.expander("What am I looking at?"):
        st.markdown("""
Each point in this 3D space represents one cell in the simulated kidney tissue:

- **Red mass** (isosurface) — the tumor. Denser red = more tumor cells packed together
- **Blue dots** — Killer T-cells (CD8) — the main tumor-fighting cells
- **Purple dots** — Natural Killer cells — innate immune cells that attack on contact
- **Orange dots** — Macrophages (M1, anti-tumor)
- **Green dots** — CD4 Helper T-cells — coordinate the immune response
- **Cyan dots** — Neutrophils — early responders
- **Pink dots** — Dendritic cells — detect the tumor and activate other immune cells
- **Gray diamonds** — Blood vessels — supply glucose (energy)

Use the sidebar controls to filter cell types, change camera angle, or view glucose distribution.
        """)

with tab_density:
    st.caption("Looking straight down through the tissue. "
               "Brighter areas have more cells stacked in that column.")
    fig_bf = spatial_density_map(agents=agents, glucose=glucose, grid_dims=grid_dims, dark_mode=dark_mode)
    fig_bf.update_layout(height=450)
    st.plotly_chart(fig_bf, use_container_width=True)

with tab_compare:
    st.caption("Pick two moments in time to see how the tissue changed.")
    if len(steps) < 2:
        st.info("Need at least 2 snapshots to compare. Try running a longer simulation.")
    else:
        cmp_cols = st.columns(2)
        with cmp_cols[0]:
            step_a = st.selectbox("Earlier step", options=steps, index=0, key="cmp_a")
        with cmp_cols[1]:
            step_b = st.selectbox("Later step", options=steps, index=len(steps) - 1, key="cmp_b")

        snap_a = _cached_load_snapshot(str(Path(snapshot_dir) / f"step_{step_a:05d}.npz"))
        snap_b = _cached_load_snapshot(str(Path(snapshot_dir) / f"step_{step_b:05d}.npz"))

        def _snap_metrics(s):
            ag = s["agents"]
            n = ag.shape[0]
            if n > 0:
                bc = np.bincount(ag[:, 3], minlength=len(AgentType))
                return {
                    "total": n,
                    "tumor": int(bc[AgentType.TUMOR_CELL]),
                    "immune": sum(int(bc[t]) for t in IMMUNE_TYPES),
                    "glucose": float(np.mean(s["glucose"])),
                }
            return {"total": 0, "tumor": 0, "immune": 0, "glucose": 0.0}

        ma, mb = _snap_metrics(snap_a), _snap_metrics(snap_b)

        # What changed
        tumor_diff = mb["tumor"] - ma["tumor"]
        immune_diff = mb["immune"] - ma["immune"]
        if tumor_diff < 0 and immune_diff > 0:
            st.success(f"Between step {step_a} and {step_b}: tumor shrank by {abs(tumor_diff):,} cells "
                       f"while immune cells grew by {immune_diff:,}.")
        elif tumor_diff > 0:
            st.warning(f"Between step {step_a} and {step_b}: tumor grew by {tumor_diff:,} cells.")

        dm1, dm2, dm3, dm4 = st.columns(4)
        dm1.metric("Total Cells", f"{mb['total']:,}",
                   delta=f"{mb['total'] - ma['total']:+,}")
        dm2.metric("Tumor", f"{mb['tumor']:,}",
                   delta=f"{mb['tumor'] - ma['tumor']:+,}", delta_color="inverse")
        dm3.metric("Immune", f"{mb['immune']:,}",
                   delta=f"{mb['immune'] - ma['immune']:+,}")
        dm4.metric("Glucose", f"{mb['glucose']:.3f}",
                   delta=f"{mb['glucose'] - ma['glucose']:+.3f}")

        bf_cols = st.columns(2)
        with bf_cols[0]:
            st.markdown(f"**Step {step_a}**")
            fig_a = spatial_density_map(agents=snap_a["agents"], glucose=snap_a["glucose"],
                                    grid_dims=snap_a["grid_dims"], dark_mode=dark_mode)
            fig_a.update_layout(height=300)
            st.plotly_chart(fig_a, use_container_width=True, key="cmp_bf_a")
        with bf_cols[1]:
            st.markdown(f"**Step {step_b}**")
            fig_b = spatial_density_map(agents=snap_b["agents"], glucose=snap_b["glucose"],
                                    grid_dims=snap_b["grid_dims"], dark_mode=dark_mode)
            fig_b.update_layout(height=300)
            st.plotly_chart(fig_b, use_container_width=True, key="cmp_bf_b")

# ---------------------------------------------------------------------------
# Cell population breakdown
# ---------------------------------------------------------------------------

with st.expander("Cell count breakdown", icon=":material/table_chart:"):
    if counts_by_type:
        rows = []
        for tid, cnt in sorted(counts_by_type.items(), key=lambda x: -x[1]):
            name = CELL_TYPE_NAMES.get(tid, AGENT_TYPE_VIS.get(tid, _DEFAULT_VIS).name)
            pct = (cnt / n_agents * 100) if n_agents > 0 else 0
            category = "Tumor" if tid == AgentType.TUMOR_CELL else (
                "Immune" if tid in IMMUNE_TYPES else "Other")
            rows.append({
                "Cell Type": name,
                "Role": category,
                "Count": cnt,
                "Share": f"{pct:.1f}%",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.write("No cells in this snapshot.")

"""Glucose Field Visualization — 3D and 2D views of energy distribution in tissue."""

from pathlib import Path
import numpy as np
import streamlit as st
import plotly.graph_objects as go

from ui.lib.charts import AgentType, environment_3d, spatial_density_map
from ui.lib.state import load_snapshot, find_snapshot_runs, list_snapshot_steps, read_meta
from ui.lib.formatting import TREATMENT_LABELS

st.title("Glucose Field Explorer")
st.caption("Explore the energy (glucose) distribution in the 3D tissue. "
           "Glucose is the fuel for all cells — tumor cells consume it heavily (Warburg effect).")

# ---------------------------------------------------------------------------
# Info Box
# ---------------------------------------------------------------------------

with st.expander("Understanding Glucose in the Simulation", expanded=False):
    st.markdown("""
    **What is glucose in this model?**
    - Glucose is the primary energy source for all cells in the tissue
    - It diffuses from blood vessels throughout the tissue
    - Tumor cells consume glucose much more rapidly than normal cells (the "Warburg effect")
    - Low glucose areas weaken immune cell effectiveness
    
    **What you'll see:**
    - **Red/orange areas**: High glucose concentration (energy-rich zones)
    - **Blue/dark areas**: Low glucose concentration (energy-starved zones)
    - **Blood vessels**: Sources of glucose that replenish the tissue
    - **Tumor masses**: Create "glucose sinks" that deplete local energy
    
    **Why it matters:**
    - Tumor cells need glucose to grow and divide
    - Immune cells need glucose to move and attack effectively
    - TKI treatment can cut off glucose supply by blocking angiogenesis
    - Glucose gradients create competitive dynamics between cell types
    """)

# ---------------------------------------------------------------------------
# Run and snapshot selection
# ---------------------------------------------------------------------------

# Find runs with snapshots
snapshot_runs = find_snapshot_runs()
if not snapshot_runs:
    st.error("""
    **No snapshot data available.** To explore glucose fields, you need to:
    
    1. Run a simulation with snapshots enabled (use `--snapshot 10` in CLI)
    2. Or use the web UI and enable snapshots in the Run page
    
    Snapshots capture the 3D state of the tissue every few steps, including glucose concentrations.
    """)
    if st.button("Go to Run Page", type="primary"):
        st.switch_page("pages/2_run.py")
    st.stop()

# Run selector
run_options = {}
for run_dir, meta in snapshot_runs:
    treatment = meta.get("treatment", "?")
    sex = "F" if meta.get("sex") == "F" else "M"
    outcome = meta.get("outcome", "?")
    outcome_icon = "✅" if outcome == "SURVIVAL" else ("❌" if outcome == "PROGRESSION" else "❓")
    label = f"{outcome_icon} {TREATMENT_LABELS.get(treatment, treatment)} | {sex}, BMI {meta.get('BMI', '?')}"
    run_options[label] = (run_dir, meta)

if not run_options:
    st.error("No valid snapshot runs found.")
    st.stop()

selected_label = st.selectbox(
    "Select a simulation run", list(run_options.keys()), key="glucose_run_select"
)
selected_run_dir, selected_meta = run_options[selected_label]

# Get available snapshot steps
snapshot_steps = list_snapshot_steps(selected_run_dir)
if not snapshot_steps:
    st.error(f"No snapshots found for selected run: {selected_run_dir}")
    st.stop()

st.markdown(f"**{len(snapshot_steps)} snapshots available** (steps: {min(snapshot_steps)} to {max(snapshot_steps)})")

# Step selector
step_col, info_col = st.columns([1, 2])
with step_col:
    selected_step = st.select_slider(
        "Snapshot step",
        options=snapshot_steps,
        key="glucose_step_select",
        format_func=lambda s: f"Step {s}"
    )

with info_col:
    treatment_start = selected_meta.get("treatment_start", 0)
    treatment = selected_meta.get("treatment", "None")
    
    if treatment != "None" and selected_step < treatment_start:
        st.info(f"**Pre-treatment phase** — {TREATMENT_LABELS.get(treatment, treatment)} starts at step {treatment_start}")
    elif treatment != "None" and selected_step >= treatment_start:
        st.success(f"**{TREATMENT_LABELS.get(treatment, treatment)} active** since step {treatment_start}")
    else:
        st.caption(f"**No treatment** — natural immune response only")

# ---------------------------------------------------------------------------
# Load snapshot data
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading snapshot data...")
def load_glucose_data(run_dir: str, step: int):
    snapshot = load_snapshot(run_dir, step)
    if not snapshot:
        return None, None, None
    
    agents = snapshot["agents"]
    glucose = snapshot.get("glucose")
    grid_dims = snapshot["grid_dims"]
    
    if glucose is None:
        return agents, None, grid_dims
    
    return agents, glucose, grid_dims

agents, glucose, grid_dims = load_glucose_data(selected_run_dir, selected_step)

if agents is None:
    st.error(f"Could not load snapshot for step {selected_step}")
    st.stop()

if glucose is None:
    st.warning("""
    **Glucose data not found in snapshot.** The simulation may have been run without glucose field tracking.
    
    To get glucose data, ensure your simulation includes glucose field monitoring.
    """)
    st.stop()

# ---------------------------------------------------------------------------
# Glucose Statistics
# ---------------------------------------------------------------------------

st.subheader("Glucose Field Statistics")

# Compute glucose statistics
glucose_mean = np.mean(glucose)
glucose_std = np.std(glucose)
glucose_min = np.min(glucose)
glucose_max = np.max(glucose)
glucose_total = np.sum(glucose)

# Count cells by type
cell_counts = {}
if len(agents) > 0:
    unique_types, counts = np.unique(agents[:, 3], return_counts=True)
    for type_id, count in zip(unique_types, counts):
        try:
            agent_type = AgentType(type_id)
            cell_counts[agent_type] = count
        except ValueError:
            cell_counts[f"Unknown_{type_id}"] = count

# Metrics display
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Mean Glucose", f"{glucose_mean:.3f}")
m2.metric("Std Dev", f"{glucose_std:.3f}")
m3.metric("Range", f"{glucose_min:.3f} - {glucose_max:.3f}")
m4.metric("Total Energy", f"{glucose_total:.0f}")
m5.metric("Grid Size", f"{grid_dims[0]}×{grid_dims[1]}×{grid_dims[2]}")

# Cell counts
if cell_counts:
    st.markdown("**Cell populations at this step:**")
    cc_cols = st.columns(min(len(cell_counts), 6))
    for i, (cell_type, count) in enumerate(list(cell_counts.items())[:6]):
        if hasattr(cell_type, 'name'):
            name = cell_type.name.replace('_', ' ').title()
        else:
            name = str(cell_type)
        cc_cols[i % len(cc_cols)].metric(name, f"{count:,}")

st.divider()

# ---------------------------------------------------------------------------
# 3D Visualization Controls
# ---------------------------------------------------------------------------

st.subheader("3D Glucose + Cells Visualization")

# Controls
ctrl_cols = st.columns([1, 1, 1, 1])
with ctrl_cols[0]:
    show_cells = st.checkbox("Show Cells", value=True, key="glucose_show_cells")
with ctrl_cols[1]:
    glucose_opacity = st.slider("Glucose Opacity", 0.1, 1.0, 0.5, 0.1, key="glucose_opacity")
with ctrl_cols[2]:
    cell_size = st.slider("Cell Size", 1, 8, 3, key="glucose_cell_size")
with ctrl_cols[3]:
    glucose_threshold = st.slider("Glucose Threshold", glucose_min, glucose_max, glucose_mean, key="glucose_threshold")

# Glucose slice controls
st.markdown("**Glucose slice planes** (optional):")
slice_cols = st.columns(3)
with slice_cols[0]:
    x_slice = st.number_input("X slice", 0, grid_dims[0]-1, value=None, placeholder="Off", key="glucose_x_slice")
with slice_cols[1]:
    y_slice = st.number_input("Y slice", 0, grid_dims[1]-1, value=None, placeholder="Off", key="glucose_y_slice")
with slice_cols[2]:
    z_slice = st.number_input("Z slice", 0, grid_dims[2]-1, value=None, placeholder="Off", key="glucose_z_slice")

# Build glucose slices dict
glucose_slices = {}
if x_slice is not None:
    glucose_slices["x"] = x_slice
if y_slice is not None:
    glucose_slices["y"] = y_slice
if z_slice is not None:
    glucose_slices["z"] = z_slice

# Create 3D visualization
@st.cache_data(show_spinner="Generating 3D visualization...")
def create_glucose_3d(agents, glucose, grid_dims, show_cells, cell_size, glucose_slices, glucose_threshold, glucose_opacity):
    # Filter agents if showing cells
    visible_agents = agents if show_cells else np.array([]).reshape(0, 4)
    
    # Create the visualization
    fig = environment_3d(
        visible_agents,
        glucose,
        grid_dims,
        visible_types=None,  # Show all cell types
        marker_size=cell_size,
        glucose_slices=glucose_slices if glucose_slices else None,
        dark_mode=False
    )
    
    # Add glucose isosurface
    if glucose_threshold < glucose_max:
        w, h, d = grid_dims
        gx, gy, gz = np.mgrid[0:w, 0:h, 0:d]
        
        fig.add_trace(go.Isosurface(
            x=gx.flatten(),
            y=gy.flatten(), 
            z=gz.flatten(),
            value=glucose.flatten(),
            isomin=glucose_threshold,
            isomax=glucose_max,
            surface_count=3,
            colorscale="YlOrRd",
            opacity=glucose_opacity,
            caps=dict(x_show=False, y_show=False, z_show=False),
            colorbar=dict(title="Glucose<br>Concentration", x=1.02),
            name=f"Glucose ≥ {glucose_threshold:.3f}",
            hovertemplate="Glucose: %{value:.3f}<extra>Energy Field</extra>",
        ))
    
    # Update layout
    fig.update_layout(
        title=f"Glucose Field and Cells at Step {selected_step}",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y", 
            zaxis_title="Z",
            aspectmode='cube',
            bgcolor="rgba(240,240,240,0.1)"
        ),
        height=600,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

fig_3d = create_glucose_3d(agents, glucose, grid_dims, show_cells, cell_size, glucose_slices, glucose_threshold, glucose_opacity)
st.plotly_chart(fig_3d, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# 2D Cross-sections
# ---------------------------------------------------------------------------

st.subheader("2D Cross-Section Views")
st.caption("View glucose concentrations as 2D slices through the tissue.")

# 2D controls
view_axis = st.selectbox("View axis", ["XY (top-down)", "XZ (side)", "YZ (front)"], key="glucose_2d_axis")
axis_map = {"XY (top-down)": 2, "XZ (side)": 1, "YZ (front)": 0}
slice_axis = axis_map[view_axis]
axis_name = view_axis.split()[0]
max_slice = grid_dims[slice_axis] - 1

slice_pos = st.slider(f"Slice position along {axis_name[-1]} axis", 0, max_slice, max_slice // 2, key="glucose_2d_slice")

# Create 2D slice
@st.cache_data(show_spinner="Creating 2D slice...")
def create_glucose_2d(glucose, slice_axis, slice_pos, view_axis):
    # Extract 2D slice
    if slice_axis == 0:  # YZ view
        slice_2d = glucose[slice_pos, :, :]
        x_label, y_label = "Y", "Z"
    elif slice_axis == 1:  # XZ view  
        slice_2d = glucose[:, slice_pos, :]
        x_label, y_label = "X", "Z"
    else:  # XY view
        slice_2d = glucose[:, :, slice_pos]
        x_label, y_label = "X", "Y"
    
    fig = go.Figure(data=go.Heatmap(
        z=slice_2d.T,  # Transpose for correct orientation
        colorscale="YlOrRd",
        colorbar=dict(title="Glucose<br>Concentration"),
        hovertemplate=f"{x_label}: %{{x}}<br>{y_label}: %{{y}}<br>Glucose: %{{z:.3f}}<extra></extra>",
    ))
    
    fig.update_layout(
        title=f"Glucose {view_axis} slice at position {slice_pos}",
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=400,
        yaxis=dict(scaleanchor="x", scaleratio=1)  # Square aspect ratio
    )
    
    return fig

fig_2d = create_glucose_2d(glucose, slice_axis, slice_pos, view_axis)
st.plotly_chart(fig_2d, use_container_width=True)

# ---------------------------------------------------------------------------
# Glucose Analysis
# ---------------------------------------------------------------------------

st.subheader("Glucose Spatial Analysis")

analysis_cols = st.columns(2)

with analysis_cols[0]:
    st.markdown("**Distribution Statistics:**")
    
    # Histogram data
    hist_bins = 20
    counts, bins = np.histogram(glucose.flatten(), bins=hist_bins)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    
    fig_hist = go.Figure(go.Bar(
        x=bin_centers,
        y=counts,
        marker_color="orange",
        opacity=0.7,
        name="Glucose Distribution"
    ))
    fig_hist.update_layout(
        title="Glucose Concentration Distribution",
        xaxis_title="Glucose Level",
        yaxis_title="Number of Voxels",
        height=300,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with analysis_cols[1]:
    st.markdown("**Spatial Gradients:**")
    
    # Calculate gradients
    try:
        grad_x = np.gradient(glucose, axis=0)
        grad_y = np.gradient(glucose, axis=1)  
        grad_z = np.gradient(glucose, axis=2)
        
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        # Gradient statistics
        grad_mean = np.mean(gradient_magnitude)
        grad_max = np.max(gradient_magnitude)
        grad_std = np.std(gradient_magnitude)
        
        st.metric("Mean Gradient", f"{grad_mean:.4f}")
        st.metric("Max Gradient", f"{grad_max:.4f}")  
        st.metric("Gradient Std", f"{grad_std:.4f}")
        
        st.caption("Higher gradients indicate steeper changes in glucose concentration, "
                  "often found near blood vessels or tumor masses.")
        
    except Exception as e:
        st.error(f"Could not calculate gradients: {e}")

# ---------------------------------------------------------------------------
# Summary and Next Steps
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Interpretation Guide")

with st.container(border=True):
    st.markdown("""
    **What to look for in glucose patterns:**
    
    🔴 **High glucose areas (red/orange):**
    - Near blood vessels (glucose sources)
    - Areas with fewer cells (less consumption)
    - May attract more tumor growth
    
    🔵 **Low glucose areas (blue/dark):**
    - Far from blood vessels
    - Near large tumor masses (high consumption) 
    - May limit immune cell effectiveness
    
    📈 **Steep gradients:**
    - Competition boundaries between tumor and immune cells
    - Blood vessel proximity effects
    - Treatment impact zones (TKI affects blood supply)
    
    💡 **Analysis tips:**
    - Compare pre-treatment vs post-treatment snapshots
    - Look for glucose "deserts" created by large tumors
    - Check if treatment changes glucose distribution patterns
    """)

# Navigation buttons
nav_cols = st.columns(3)
with nav_cols[0]:
    if st.button("← Back to Results", use_container_width=True):
        st.switch_page("pages/3_results.py")
with nav_cols[1]:  
    if st.button("View 3D Environment", use_container_width=True):
        st.switch_page("pages/5_environment.py")
with nav_cols[2]:
    if st.button("Compare Runs", use_container_width=True):
        st.switch_page("pages/4_history.py")
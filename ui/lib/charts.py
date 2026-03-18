# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Plotly chart builders and color constants for RCC simulation results."""

from __future__ import annotations

import copy
import importlib
import types
from typing import TYPE_CHECKING, NamedTuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.lib.formatting import format_column_name, format_kill_column_name

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd

# Load AgentType directly from the module file, bypassing src.agents.__init__
# which transitively imports repast4py → numpy (incompatible C-extensions).
def _load_agent_type():
    """Load AgentType enum directly from file, bypassing heavy transitive imports."""
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "agent_types",
        Path(__file__).resolve().parents[2] / "src" / "agents" / "agent_types.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.AgentType

AgentType = _load_agent_type()
del _load_agent_type


class AgentVis(NamedTuple):
    color: str
    name: str
    size: int
    symbol: str

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

CELL_COLORS = {
    "tumor_cells": "#DC2626",
    "cytotoxic_t_cells": "#2563EB",
    "cd8_naive": "#60A5FA",
    "cd4_naive": "#16A34A",
    "th1": "#22C55E",
    "th2": "#86EFAC",
    "treg": "#4ADE80",
    "dendritic": "#D946EF",
    "pdc": "#F0ABFC",
    "m1": "#EA580C",
    "m2": "#FB923C",
    "nk": "#7C3AED",
    "mast": "#EC4899",
    "neutrophil": "#06B6D4",
    "blood": "#94A3B8",
}

KILL_COLORS = {
    "apoptosis_count": "#DC2626",
    "ctc_kills": "#2563EB",
    "nkl_kills": "#7C3AED",
    "m1_kills": "#EA580C",
    "dc_kills": "#D946EF",
    "pdc_kills": "#F0ABFC",
    "neutrophil_kills": "#06B6D4",
}

GLUCOSE_COLOR = "#F59E0B"
TREATMENT_COLOR = "rgba(13, 115, 119, 0.5)"

KILL_COLS = [
    "apoptosis_count", "ctc_kills", "nkl_kills", "m1_kills",
    "dc_kills", "pdc_kills", "neutrophil_kills",
]

GLUCOSE_COLS = ["mean_glucose", "total_glucose", "min_glucose", "max_glucose"]
GLUCOSE_ANALYSIS_COLS = [
    "glucose_presence_confirmed", "glucose_coverage_percent", "glucose_detection_confidence",
    "glucose_gradient_mean_magnitude", "glucose_gradient_max_magnitude", "glucose_gradient_uniformity",
    "glucose_hotspots_count", "glucose_hotspots_coverage"
]
ALL_GLUCOSE_COLS = GLUCOSE_COLS + GLUCOSE_ANALYSIS_COLS

NON_CELL_COLS = {"step"} | set(KILL_COLS) | set(GLUCOSE_COLS)

# Cell classification — used across pages to distinguish immune from non-immune
NON_IMMUNE = frozenset({
    AgentType.TUMOR_CELL, AgentType.ADIPOCYTE, AgentType.BLOOD,
    AgentType.SEX_HORMONE, AgentType.CYTOKINE,
})
IMMUNE_TYPES = frozenset(t for t in AgentType if t not in NON_IMMUNE)

COMPARISON_PALETTE = ["#DC2626", "#2563EB", "#16A34A", "#7C3AED", "#EA580C", "#EC4899"]

LAYOUT_DEFAULTS = dict(
    template="plotly_white",
    font=dict(family="Inter, sans-serif", color="#1A2332"),
    margin=dict(l=60, r=30, t=50, b=50),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


def _base_layout(**overrides):
    """Return a copy of LAYOUT_DEFAULTS merged with any overrides."""
    layout = copy.deepcopy(LAYOUT_DEFAULTS)
    layout.update(overrides)
    return layout


# ---------------------------------------------------------------------------
# Population dynamics
# ---------------------------------------------------------------------------

def population_dynamics(df: pd.DataFrame, selected_types: list[str] | None = None,
                        log_scale: bool = False) -> go.Figure:
    """Line chart of all cell populations over simulation steps.

    Args:
        df: Simulation log DataFrame with a 'step' column and cell count columns.
        selected_types: Subset of column names to plot, or None for all.
        log_scale: Use logarithmic y-axis.

    Returns:
        Plotly Figure with one trace per cell type.
    """
    cell_cols = [c for c in df.columns if c not in NON_CELL_COLS]
    if selected_types:
        cell_cols = [c for c in cell_cols if c in selected_types]

    fig = go.Figure()
    for col in cell_cols:
        color = CELL_COLORS.get(col, None)
        fig.add_trace(go.Scatter(
            x=df["step"], y=df[col],
            name=format_column_name(col),
            line=dict(color=color, width=2),
            hovertemplate="%{y:,.0f}",
        ))

    layout_kwargs = dict(
        title="Cell Populations Over Time",
        xaxis_title="Simulation Step",
        yaxis_title="Number of Cells",
    )
    if log_scale:
        layout_kwargs["yaxis_type"] = "log"

    fig.update_layout(**_base_layout(**layout_kwargs))
    return fig


# ---------------------------------------------------------------------------
# Tumor growth
# ---------------------------------------------------------------------------

def tumor_growth(df: pd.DataFrame, treatment_start: int | None = None) -> go.Figure:
    """Area chart of tumor cell count over time with peak annotation.

    Args:
        df: Simulation log DataFrame.
        treatment_start: Step at which treatment begins (adds vertical line).

    Returns:
        Plotly Figure showing tumor growth trajectory.
    """
    fig = go.Figure()
    tumor_color = CELL_COLORS["tumor_cells"]

    fig.add_trace(go.Scatter(
        x=df["step"], y=df["tumor_cells"],
        name="Tumor Cells",
        line=dict(color=tumor_color, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(220, 38, 38, 0.15)",
        hovertemplate="%{y:,.0f}",
    ))

    if treatment_start is not None and treatment_start < df["step"].max():
        fig.add_vline(
            x=treatment_start, line_dash="dash",
            line_color=TREATMENT_COLOR, line_width=2,
            annotation_text="Treatment Start",
            annotation_position="top right",
        )

    peak = df["tumor_cells"].max()
    peak_step = df.loc[df["tumor_cells"].idxmax(), "step"]
    final = df["tumor_cells"].iloc[-1]

    fig.add_annotation(
        x=peak_step, y=peak,
        text=f"Peak: {peak:,.0f}",
        showarrow=True, arrowhead=2,
        font=dict(size=11, color=tumor_color),
    )

    fig.update_layout(**_base_layout(
        title=f"Tumor Size Over Time  (Final: {final:,.0f} cells)",
        xaxis_title="Simulation Step",
        yaxis_title="Number of Tumor Cells",
    ))
    return fig


# ---------------------------------------------------------------------------
# Kill counts
# ---------------------------------------------------------------------------

def kill_counts(df: pd.DataFrame, stacked: bool = False) -> go.Figure:
    """Cumulative kill count chart by immune cell type.

    Args:
        df: Simulation log DataFrame.
        stacked: Stack traces to show total immune activity.

    Returns:
        Plotly Figure with one trace per kill column.
    """
    existing = [c for c in KILL_COLS if c in df.columns]
    fig = go.Figure()

    for col in existing:
        color = KILL_COLORS.get(col, None)
        kwargs = {}
        if stacked:
            kwargs["stackgroup"] = "kills"
        fig.add_trace(go.Scatter(
            x=df["step"], y=df[col],
            name=format_column_name(col),
            line=dict(color=color, width=2),
            hovertemplate="%{y:,.0f}",
            **kwargs,
        ))

    fig.update_layout(**_base_layout(
        title="Tumor Cells Destroyed Over Time",
        xaxis_title="Simulation Step",
        yaxis_title="Total Kills (cumulative)",
    ))
    return fig


def kill_rate(df: pd.DataFrame) -> go.Figure:
    """Kill rate (derivative) — kills per step for each immune cell type."""
    existing = [c for c in KILL_COLS if c in df.columns]
    fig = go.Figure()

    for col in existing:
        color = KILL_COLORS.get(col, None)
        rate = df[col].diff().fillna(0).clip(lower=0)
        fig.add_trace(go.Scatter(
            x=df["step"], y=rate,
            name=format_column_name(col),
            line=dict(color=color, width=2),
            hovertemplate="%{y:,.0f} kills/step",
        ))

    fig.update_layout(**_base_layout(
        title="Kill Rate — Kills Per Step",
        xaxis_title="Simulation Step",
        yaxis_title="Kills per Step",
    ))
    return fig


# ---------------------------------------------------------------------------
# Glucose
# ---------------------------------------------------------------------------

def glucose_dashboard(df: pd.DataFrame) -> go.Figure:
    """2x2 subplot dashboard of basic glucose metrics over time."""
    existing = [c for c in GLUCOSE_COLS if c in df.columns]
    if not existing:
        fig = go.Figure()
        fig.add_annotation(text="No glucose data available", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5, font=dict(size=16))
        return fig

    titles = {
        "mean_glucose": "Average Glucose",
        "total_glucose": "Total Glucose in Tissue",
        "min_glucose": "Lowest Glucose",
        "max_glucose": "Highest Glucose",
    }

    rows, cols = 2, 2
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[titles.get(c, c) for c in GLUCOSE_COLS if c in existing],
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    for i, col in enumerate(c for c in GLUCOSE_COLS if c in existing):
        r, c_idx = divmod(i, 2)
        fig.add_trace(
            go.Scatter(
                x=df["step"], y=df[col],
                name=titles.get(col, col),
                line=dict(color=GLUCOSE_COLOR, width=2),
                showlegend=False,
                hovertemplate="%{y:.3f}",
            ),
            row=r + 1, col=c_idx + 1,
        )

    fig.update_layout(**_base_layout(
        title="Glucose (Energy) Levels in the Tissue",
        height=500,
    ))
    return fig


def glucose_analysis_dashboard(df: pd.DataFrame) -> go.Figure:
    """Enhanced glucose analysis dashboard for professor's requirements."""
    existing_analysis = [c for c in GLUCOSE_ANALYSIS_COLS if c in df.columns]
    if not existing_analysis:
        fig = go.Figure()
        fig.add_annotation(text="No glucose analysis data available", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5, font=dict(size=16))
        return fig

    analysis_titles = {
        "glucose_presence_confirmed": "Glucose Presence Detection",
        "glucose_coverage_percent": "Glucose Coverage (%)",
        "glucose_detection_confidence": "Detection Confidence",
        "glucose_gradient_mean_magnitude": "Mean Gradient Magnitude",
        "glucose_gradient_max_magnitude": "Max Gradient Magnitude",
        "glucose_gradient_uniformity": "Gradient Uniformity",
        "glucose_hotspots_count": "Glucose Hotspots Count",
        "glucose_hotspots_coverage": "Hotspots Coverage (%)",
    }

    # Select up to 6 most important metrics for display
    priority_metrics = [
        "glucose_coverage_percent", "glucose_detection_confidence", 
        "glucose_gradient_mean_magnitude", "glucose_gradient_uniformity",
        "glucose_hotspots_count", "glucose_hotspots_coverage"
    ]
    display_metrics = [c for c in priority_metrics if c in existing_analysis][:6]

    rows, cols = 2, 3
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[analysis_titles.get(c, c) for c in display_metrics],
        vertical_spacing=0.15,
        horizontal_spacing=0.08,
    )

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
    
    for i, col in enumerate(display_metrics):
        r, c_idx = divmod(i, 3)
        
        # Special handling for boolean presence confirmed
        if col == "glucose_presence_confirmed" and col in df.columns:
            y_data = df[col].astype(int)  # Convert bool to int for plotting
        else:
            y_data = df[col] if col in df.columns else []
            
        fig.add_trace(
            go.Scatter(
                x=df["step"], y=y_data,
                name=analysis_titles.get(col, col),
                line=dict(color=colors[i % len(colors)], width=2),
                showlegend=False,
                hovertemplate="%{y:.3f}",
            ),
            row=r + 1, col=c_idx + 1,
        )

    fig.update_layout(**_base_layout(
        title="Advanced Glucose Analysis - Professor's Requirements",
        height=600,
    ))
    return fig


# ---------------------------------------------------------------------------
# Comparison charts (history page)
# ---------------------------------------------------------------------------

def immune_effectiveness_pie(df: pd.DataFrame) -> go.Figure:
    """Pie chart showing contribution of each immune cell type to total kills."""
    kill_cols = [c for c in KILL_COLS if c in df.columns and c != "apoptosis_count"]
    labels = [format_kill_column_name(c) for c in kill_cols]
    values = [int(df[c].iloc[-1]) for c in kill_cols]
    colors = [KILL_COLORS.get(c, "#888") for c in kill_cols]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.4,
        textinfo="label+percent",
        hovertemplate="%{label}: %{value:,} kills (%{percent})<extra></extra>",
    )])
    fig.update_layout(**_base_layout(
        title="Which Immune Cells Killed the Most Tumor Cells?",
        height=400,
        showlegend=False,
    ))
    return fig


def compare_tumor_curves(runs_data: list[tuple[str, pd.DataFrame]]) -> go.Figure:
    """Overlay tumor curves from multiple runs. runs_data = [(label, df), ...]"""
    fig = go.Figure()
    palette = COMPARISON_PALETTE
    for i, (label, df) in enumerate(runs_data):
        color = palette[i % len(palette)]
        fig.add_trace(go.Scatter(
            x=df["step"], y=df["tumor_cells"],
            name=label,
            line=dict(color=color, width=2),
            hovertemplate="%{y:,.0f}",
        ))
    fig.update_layout(**_base_layout(
        title="Tumor Size Comparison",
        xaxis_title="Simulation Step",
        yaxis_title="Number of Tumor Cells",
    ))
    return fig


def compare_glucose_curves(runs_data: list[tuple[str, pd.DataFrame]]) -> go.Figure:
    """Overlay mean glucose curves from multiple runs."""
    fig = go.Figure()
    palette = COMPARISON_PALETTE
    for i, (label, df) in enumerate(runs_data):
        if "mean_glucose" not in df.columns:
            continue
        color = palette[i % len(palette)]
        fig.add_trace(go.Scatter(
            x=df["step"], y=df["mean_glucose"],
            name=label,
            line=dict(color=color, width=2),
            hovertemplate="%{y:.3f}",
        ))
    fig.update_layout(**_base_layout(
        title="Mean Glucose Comparison",
        xaxis_title="Simulation Step",
        yaxis_title="Mean Glucose Concentration",
    ))
    return fig


def compare_population_curves(runs_data: list[tuple[str, pd.DataFrame]],
                               cell_type: str = "tumor_cells") -> go.Figure:
    """Overlay a specific cell type population from multiple runs."""
    fig = go.Figure()
    palette = COMPARISON_PALETTE
    for i, (label, df) in enumerate(runs_data):
        if cell_type not in df.columns:
            continue
        color = palette[i % len(palette)]
        fig.add_trace(go.Scatter(
            x=df["step"], y=df[cell_type],
            name=label,
            line=dict(color=color, width=2),
            hovertemplate="%{y:,.0f}",
        ))
    fig.update_layout(**_base_layout(
        title=f"{format_column_name(cell_type)} Comparison",
        xaxis_title="Simulation Step",
        yaxis_title="Cell Count",
    ))
    return fig


def compare_kills_bar(runs_data: list[tuple[str, pd.DataFrame]]) -> go.Figure:
    """Side-by-side bar chart of final kill counts."""
    fig = go.Figure()
    palette = COMPARISON_PALETTE
    all_cols = set()
    for _, df in runs_data:
        all_cols.update(df.columns)
    existing_cols = [c for c in KILL_COLS if c in all_cols]

    for i, (label, df) in enumerate(runs_data):
        finals = [int(df[c].iloc[-1]) if c in df.columns else 0 for c in existing_cols]
        fig.add_trace(go.Bar(
            name=label,
            x=[format_column_name(c) for c in existing_cols],
            y=finals,
            marker_color=palette[i % len(palette)],
        ))

    fig.update_layout(**_base_layout(
        title="Immune Kills Comparison",
        barmode="group",
        xaxis_title="Immune Cell Type",
        yaxis_title="Tumor Cells Destroyed",
    ))
    return fig


# ---------------------------------------------------------------------------
# 3D Environment visualization
# ---------------------------------------------------------------------------

_DEFAULT_VIS = AgentVis("#888888", "Unknown", 3, "circle")

AGENT_TYPE_VIS: dict[AgentType, AgentVis] = {
    AgentType.TUMOR_CELL:          AgentVis("#DC2626", "Tumor Cell", 4, "circle"),
    AgentType.CD8_CYTOTOXIC_T_CELL: AgentVis("#2563EB", "CD8 Cytotoxic T", 3, "circle"),
    AgentType.CD8_NAIVE_T_CELL:    AgentVis("#60A5FA", "CD8 Naive T", 3, "circle"),
    AgentType.CD4_NAIVE_T_CELL:    AgentVis("#16A34A", "CD4 Naive T", 3, "circle"),
    AgentType.CD4_HELPER1_T_CELL:  AgentVis("#22C55E", "CD4 Helper-1 T", 3, "circle"),
    AgentType.CD4_HELPER2_T_CELL:  AgentVis("#86EFAC", "CD4 Helper-2 T", 3, "circle"),
    AgentType.REGULATORY_T_CELL:   AgentVis("#4ADE80", "Treg", 3, "circle"),
    AgentType.DENDRITIC_CELL:      AgentVis("#D946EF", "Dendritic Cell", 3, "circle"),
    AgentType.PLASMACITOID_DC:     AgentVis("#F0ABFC", "Plasmacytoid DC", 3, "circle"),
    AgentType.MACROPHAGE_M1:       AgentVis("#EA580C", "Macrophage M1", 3, "circle"),
    AgentType.MACROPHAGE_M2:       AgentVis("#FB923C", "Macrophage M2", 3, "circle"),
    AgentType.NATURAL_KILLER:      AgentVis("#7C3AED", "Natural Killer", 3, "circle"),
    AgentType.MAST_CELL:           AgentVis("#EC4899", "Mast Cell", 3, "circle"),
    AgentType.NEUTROPHIL:          AgentVis("#06B6D4", "Neutrophil", 3, "circle"),
    AgentType.ADIPOCYTE:           AgentVis("#A3E635", "Adipocyte", 3, "circle"),
    AgentType.BLOOD:               AgentVis("#94A3B8", "Blood Vessel", 3, "diamond"),
    AgentType.SEX_HORMONE:         AgentVis("#FBBF24", "Sex Hormone", 2, "circle"),
    AgentType.CYTOKINE:            AgentVis("#A78BFA", "Cytokine", 2, "circle"),
}


_AXIS_INDEX = {"x": 0, "y": 1, "z": 2}


def _add_glucose_slice(fig, glucose: np.ndarray, axis: str, pos: int):
    """Add a glucose Surface slice plane to the figure."""
    import numpy as np
    axis_idx = _AXIS_INDEX[axis]
    if not (0 <= pos < glucose.shape[axis_idx]):
        return
    slc = np.take(glucose, pos, axis=axis_idx)
    remaining = [i for i in range(3) if i != axis_idx]
    grids = np.meshgrid(
        *(np.arange(glucose.shape[i]) for i in remaining), indexing="ij"
    )
    xyz = [None, None, None]
    xyz[axis_idx] = np.full_like(grids[0], pos, dtype=float)
    xyz[remaining[0]] = grids[0]
    xyz[remaining[1]] = grids[1]
    fig.add_trace(go.Surface(
        x=xyz[0], y=xyz[1], z=xyz[2], surfacecolor=slc,
        colorscale="YlOrRd_r", opacity=0.4, showscale=False,
        name=f"Glucose {axis.upper()}={pos}", hoverinfo="skip",
    ))


def environment_3d(
    agents: np.ndarray,
    glucose: np.ndarray,
    grid_dims: tuple[int, int, int],
    visible_types: set[int] | None = None,
    marker_size: int = 3,
    glucose_slices: dict[str, int] | None = None,
    dark_mode: bool = False,
) -> go.Figure:
    """Build a 3D visualization with isosurface for tumor + scatter for others.

    Args:
        agents: int16 array (N, 4) — [x, y, z, type_id]
        glucose: float32 array (w, h, d)
        grid_dims: (w, h, d)
        visible_types: set of type_ids to show (None = all)
        marker_size: base marker size
        glucose_slices: slice planes dict
        dark_mode: use dark theme for HUD integration
    """
    import numpy as np
    try:
        from scipy.ndimage import gaussian_filter
    except ImportError:
        gaussian_filter = None

    fig = go.Figure()
    w, h, d = grid_dims

    # Types hidden by default in live/HUD view (noise); still available via visible_types filter
    _DEFAULT_HIDDEN = frozenset({
        AgentType.ADIPOCYTE, AgentType.SEX_HORMONE, AgentType.CYTOKINE,
    })

    if agents.shape[0] > 0:
        type_ids = np.unique(agents[:, 3])

        # --- Tumor isosurface ---
        tumor_tid = int(AgentType.TUMOR_CELL)
        show_tumor = (visible_types is None or tumor_tid in visible_types)
        if show_tumor and tumor_tid in type_ids:
            tumor_mask = agents[:, 3] == tumor_tid
            tumor_pts = agents[tumor_mask]
            tumor_count = len(tumor_pts)
            if tumor_count > 0:
                density = np.zeros((w, h, d), dtype=np.float32)
                xs = np.clip(tumor_pts[:, 0], 0, w - 1)
                ys = np.clip(tumor_pts[:, 1], 0, h - 1)
                zs = np.clip(tumor_pts[:, 2], 0, d - 1)
                np.add.at(density, (xs, ys, zs), 1)
                if gaussian_filter is not None:
                    density = gaussian_filter(density, sigma=1)
                dmax = density.max()
                if dmax > 0:
                    gx, gy, gz = np.mgrid[0:w, 0:h, 0:d]
                    fig.add_trace(go.Isosurface(
                        x=gx.flatten(), y=gy.flatten(), z=gz.flatten(),
                        value=density.flatten(),
                        isomin=max(1, dmax * 0.15),
                        isomax=dmax * 0.85,
                        surface_count=2,
                        colorscale=[
                            [0.0, "#7F1D1D"],
                            [0.5, "#DC2626"],
                            [1.0, "#FCA5A5"],
                        ],
                        opacity=0.3,
                        caps=dict(x_show=False, y_show=False, z_show=False),
                        colorbar=dict(title="Tumor<br>density", thickness=10),
                        name=f"Tumor Mass ({tumor_count:,} cells)",
                        hovertemplate="density=%{value:.1f}<extra>Tumor</extra>",
                    ))

        # --- Scatter traces for non-tumor types ---
        for tid in type_ids:
            tid = int(tid)
            if tid == tumor_tid:
                continue  # already rendered as isosurface
            if visible_types is not None and tid not in visible_types:
                continue
            # Hide noisy types by default (when visible_types is None)
            if visible_types is None and tid in _DEFAULT_HIDDEN:
                continue
            vis = AGENT_TYPE_VIS.get(tid, _DEFAULT_VIS)
            mask = agents[:, 3] == tid
            pts = agents[mask]
            count = len(pts)

            is_immune = tid not in NON_IMMUNE
            is_blood = tid == AgentType.BLOOD

            if is_immune:
                sz = marker_size
                opacity = 0.85
            elif is_blood:
                sz = max(1, marker_size - 1)
                opacity = 0.3
            else:
                sz = max(1, marker_size - 1)
                opacity = 0.5

            fig.add_trace(go.Scatter3d(
                x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
                mode="markers",
                marker=dict(
                    size=sz,
                    color=vis.color,
                    symbol=vis.symbol,
                    opacity=opacity,
                    line=dict(width=0),
                ),
                name=f"{vis.name} ({count:,})",
                hovertemplate=f"{vis.name}<br>({count:,} cells)<br>x=%{{x}} y=%{{y}} z=%{{z}}<extra></extra>",
            ))

    # Glucose slice planes
    if glucose_slices:
        for axis, pos in glucose_slices.items():
            if pos is not None:
                _add_glucose_slice(fig, glucose, axis, pos)

    # Theme
    if dark_mode:
        scene_cfg = dict(
            bgcolor="rgba(11,17,32,0.95)",
            xaxis=dict(range=[0, w - 1], title="X", backgroundcolor="rgba(0,0,0,0)",
                       gridcolor="rgba(14,230,183,0.08)", showbackground=True,
                       color="#64748B"),
            yaxis=dict(range=[0, h - 1], title="Y", backgroundcolor="rgba(0,0,0,0)",
                       gridcolor="rgba(14,230,183,0.08)", showbackground=True,
                       color="#64748B"),
            zaxis=dict(range=[0, d - 1], title="Z", backgroundcolor="rgba(0,0,0,0)",
                       gridcolor="rgba(14,230,183,0.08)", showbackground=True,
                       color="#64748B"),
            aspectmode="cube",
        )
        fig.update_layout(
            paper_bgcolor="rgba(11,17,32,0)",
            plot_bgcolor="rgba(11,17,32,0)",
            margin=dict(l=0, r=0, t=10, b=0),
            height=700,
            hovermode="closest",
            scene=scene_cfg,
            font=dict(family="JetBrains Mono, monospace", color="#94A3B8", size=10),
            legend=dict(font=dict(color="#94A3B8", size=9), bgcolor="rgba(15,23,42,0.8)",
                        bordercolor="rgba(14,230,183,0.2)", borderwidth=1),
        )
    else:
        fig.update_layout(**_base_layout(
            title=None,
            margin=dict(l=0, r=0, t=30, b=0),
            height=700,
            hovermode="closest",
            scene=dict(
                xaxis=dict(range=[0, w - 1], title="X"),
                yaxis=dict(range=[0, h - 1], title="Y"),
                zaxis=dict(range=[0, d - 1], title="Z"),
                aspectmode="cube",
            ),
        ))
    return fig


# ---------------------------------------------------------------------------
# Spatial density projection (2D top-down density map)
# ---------------------------------------------------------------------------

def spatial_density_map(
    agents: np.ndarray,
    glucose: np.ndarray,
    grid_dims: tuple[int, int, int],
    dark_mode: bool = True,
) -> go.Figure:
    """2D top-down heatmap showing tumor density, immune density, and glucose.

    Projects all agents onto the XY plane and shows:
    - Red channel: tumor density
    - Blue channel: immune density
    - Background: glucose heatmap
    """
    import numpy as np
    w, h, d = grid_dims

    # Project glucose to 2D (mean along Z)
    gluc_2d = np.mean(glucose, axis=2) if glucose.ndim == 3 else glucose

    # Build density maps (vectorized)
    tumor_density = np.zeros((w, h), dtype=float)
    immune_density = np.zeros((w, h), dtype=float)

    if agents.shape[0] > 0:
        xs = agents[:, 0].astype(int)
        ys = agents[:, 1].astype(int)
        tids = agents[:, 3].astype(int)
        valid = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h)

        # Tumor density
        tumor_mask = valid & (tids == AgentType.TUMOR_CELL)
        if tumor_mask.any():
            np.add.at(tumor_density, (xs[tumor_mask], ys[tumor_mask]), 1)

        # Immune density (anything not in NON_IMMUNE)
        non_immune_ids = np.array(list(NON_IMMUNE), dtype=int)
        immune_mask = valid & ~np.isin(tids, non_immune_ids)
        if immune_mask.any():
            np.add.at(immune_density, (xs[immune_mask], ys[immune_mask]), 1)

    fig = make_subplots(rows=1, cols=3,
                        subplot_titles=["Tumor Cells (top-down)", "Immune Cells (top-down)", "Glucose Level (top-down)"],
                        horizontal_spacing=0.06)

    # Tumor density heatmap
    fig.add_trace(go.Heatmap(
        z=tumor_density.T, colorscale=[[0, "#1A1A1A"], [0.01, "#1A1A1A"],
                                        [0.3, "#7F1D1D"], [0.6, "#DC2626"], [1, "#FCA5A5"]],
        showscale=True, hovertemplate="x=%{x} y=%{y}<br>Tumor cells: %{z:.0f}<extra></extra>",
        colorbar=dict(title="cells/col", thickness=10, len=0.9, x=0.28, tickfont=dict(size=9)),
    ), row=1, col=1)

    # Immune infiltrate density heatmap
    fig.add_trace(go.Heatmap(
        z=immune_density.T, colorscale=[[0, "#1A1A1A"], [0.01, "#1A1A1A"],
                                         [0.3, "#1E3A5F"], [0.6, "#2563EB"], [1, "#93C5FD"]],
        showscale=True, hovertemplate="x=%{x} y=%{y}<br>Immune cells: %{z:.0f}<extra></extra>",
        colorbar=dict(title="cells/col", thickness=10, len=0.9, x=0.635, tickfont=dict(size=9)),
    ), row=1, col=2)

    # Glucose concentration heatmap
    fig.add_trace(go.Heatmap(
        z=gluc_2d.T, colorscale=[[0, "#1C1917"], [0.3, "#78350F"],
                                   [0.6, "#F59E0B"], [1, "#FEF3C7"]],
        showscale=True, hovertemplate="x=%{x} y=%{y}<br>Glucose conc.: %{z:.3f}<extra></extra>",
        colorbar=dict(title="mean conc.", thickness=10, len=0.9, x=0.99, tickfont=dict(size=9)),
    ), row=1, col=3)

    if dark_mode:
        fig.update_layout(
            paper_bgcolor="rgba(11,17,32,0)",
            plot_bgcolor="rgba(15,23,42,0.6)",
            font=dict(family="JetBrains Mono, monospace", color="#94A3B8", size=10),
            height=280,
            margin=dict(l=30, r=40, t=35, b=35),
            showlegend=False,
        )
        for ann in fig.layout.annotations:
            ann.font.color = "#0EE6B7"
            ann.font.size = 10
        # Colorbar font colors for dark mode
        for trace in fig.data:
            if hasattr(trace, "colorbar") and trace.colorbar is not None:
                trace.colorbar.tickfont.color = "#94A3B8"
                trace.colorbar.title.font = dict(color="#94A3B8", size=9)
    else:
        fig.update_layout(**_base_layout(
            height=300,
            margin=dict(l=30, r=40, t=35, b=35),
            showlegend=False,
        ))

    # Sparse axis labels
    tick_x = list(range(0, w, max(1, w // 5)))
    tick_y = list(range(0, h, max(1, h // 5)))
    fig.update_xaxes(showticklabels=True, tickvals=tick_x, tickfont=dict(size=9),
                     title_text="X", title_font=dict(size=9))
    fig.update_yaxes(showticklabels=True, tickvals=tick_y, tickfont=dict(size=9),
                     title_text="Y", title_font=dict(size=9))
    return fig

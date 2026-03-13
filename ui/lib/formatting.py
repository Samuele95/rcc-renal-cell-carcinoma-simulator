"""Shared formatting helpers for the RCC Simulation UI."""

import functools

import streamlit as st

# ---------------------------------------------------------------------------
# Treatment display
# ---------------------------------------------------------------------------

TREATMENT_LABELS = {
    "None": "Untreated",
    "ICI": "Immunotherapy",
    "TKI": "Targeted therapy",
    "ICI+TKI": "Combination",
}

TREATMENT_INFO = {
    "None": ("No treatment — the tumor grows with only the body's natural immune response to fight it.", "treatment-none"),
    "ICI": ("Immunotherapy (ICI) — removes the 'brakes' on immune cells so they can attack the tumor more effectively.", "treatment-ici"),
    "TKI": ("Targeted therapy (TKI) — blocks the signals tumors use to grow blood vessels and feed themselves.", "treatment-tki"),
    "ICI+TKI": ("Combination therapy — uses both immunotherapy and targeted therapy together for a stronger effect.", "treatment-combo"),
}


def treatment_badge_html(treatment: str) -> str:
    desc, cls = TREATMENT_INFO.get(treatment, ("", "treatment-none"))
    label = TREATMENT_LABELS.get(treatment, treatment)
    return f'<span class="treatment-badge {cls}" role="status" aria-label="Treatment: {label}">{treatment}</span>'


# ---------------------------------------------------------------------------
# Outcome display
# ---------------------------------------------------------------------------

_OUTCOME_CONFIG = {
    "SURVIVAL": ("badge-survival", "\u2705 TUMOR ELIMINATED"),
    "PROGRESSION": ("badge-progression", "\u274c TUMOR GREW"),
    "UNKNOWN": ("badge-unknown", "\u2753 INCONCLUSIVE"),
}


def render_outcome_badge(outcome: str):
    """Render an outcome badge via st.markdown, or st.warning for unknown outcomes."""
    cfg = _OUTCOME_CONFIG.get(outcome)
    if cfg:
        cls, text = cfg
        st.markdown(f'<span class="{cls}" role="status" aria-label="Outcome: {outcome}">{text}</span>', unsafe_allow_html=True)
    else:
        st.warning(f"Outcome: {outcome}")


def outcome_badge_html(outcome: str, font_size: str = "1.1rem", padding: str = "6px 20px") -> str:
    """Return raw HTML for an outcome badge (for use in custom layouts)."""
    cfg = _OUTCOME_CONFIG.get(outcome)
    if cfg:
        cls, text = cfg
        return f'<span class="{cls}" role="status" aria-label="Outcome: {outcome}" style="font-size:{font_size};padding:{padding}">{text}</span>'
    return outcome


# ---------------------------------------------------------------------------
# Sex display
# ---------------------------------------------------------------------------

def format_sex(sex: str) -> str:
    if sex == "F":
        return "Female"
    if sex == "M":
        return "Male"
    return "?"


# ---------------------------------------------------------------------------
# Column name formatting
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=128)
def format_column_name(col: str) -> str:
    """Convert column name to friendly display name."""
    if col in _COLUMN_FRIENDLY_NAMES:
        return _COLUMN_FRIENDLY_NAMES[col]
    return col.replace("_", " ").title()


_KILL_FRIENDLY_NAMES = {
    "apoptosis_count": "Natural Death",
    "ctc_kills": "Killer T-Cell",
    "nkl_kills": "Natural Killer",
    "m1_kills": "Macrophage (M1)",
    "dc_kills": "Dendritic Cell",
    "pdc_kills": "Plasmacytoid DC",
    "neutrophil_kills": "Neutrophil",
}

_COLUMN_FRIENDLY_NAMES = {
    "tumor_cells": "Tumor Cells",
    "cytotoxic_t_cells": "Killer T-Cells (CD8)",
    "cd8_naive": "Naive CD8 T-Cells",
    "cd4_naive": "Naive CD4 T-Cells",
    "th1": "Helper T-Cells (Th1)",
    "th2": "Helper T-Cells (Th2)",
    "treg": "Regulatory T-Cells",
    "dendritic": "Dendritic Cells",
    "pdc": "Plasmacytoid DC",
    "m1": "Macrophages (M1)",
    "m2": "Macrophages (M2)",
    "nk": "Natural Killer Cells",
    "mast": "Mast Cells",
    "neutrophil": "Neutrophils",
    "blood": "Blood Vessels",
    "apoptosis_count": "Natural Death",
    "ctc_kills": "Killer T-Cell Kills",
    "nkl_kills": "NK Cell Kills",
    "m1_kills": "Macrophage Kills",
    "dc_kills": "Dendritic Cell Kills",
    "pdc_kills": "PDC Kills",
    "neutrophil_kills": "Neutrophil Kills",
    "mean_glucose": "Average Glucose",
    "total_glucose": "Total Glucose",
    "min_glucose": "Minimum Glucose",
    "max_glucose": "Maximum Glucose",
}


@functools.lru_cache(maxsize=64)
def format_kill_column_name(col: str) -> str:
    """Format kill column name to friendly display name."""
    if col in _KILL_FRIENDLY_NAMES:
        return _KILL_FRIENDLY_NAMES[col]
    return col.replace("_kills", "").replace("_count", "").replace("_", " ").title()


# ---------------------------------------------------------------------------
# Dataframe styling
# ---------------------------------------------------------------------------

OUTCOME_FRIENDLY = {
    "SURVIVAL": "\u2705 Tumor eliminated",
    "PROGRESSION": "\u274c Tumor grew",
    "UNKNOWN": "\u2753 Inconclusive",
}


def style_outcome(val: str) -> str:
    """Return CSS inline style for outcome values in pandas DataFrame styling."""
    if "eliminated" in val:
        return "background-color: #D1FAE5; color: #065F46; font-weight: 600"
    elif "grew" in val:
        return "background-color: #FEE2E2; color: #991B1B; font-weight: 600"
    return ""

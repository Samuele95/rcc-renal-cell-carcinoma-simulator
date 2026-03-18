# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Parameter configuration page — user-friendly simulation setup."""

import streamlit as st

from ui.lib.state import (
    load_all_defaults,
    load_all_labels,
    load_all_steps,
    load_optimized_preset,
    load_scenario_presets,
    get_dimension_from_volume,
    params_to_yaml,
    yaml_to_params,
)
from ui.lib.formatting import TREATMENT_INFO, TREATMENT_LABELS, treatment_badge_html, format_sex, format_column_name


# ---------------------------------------------------------------------------
# Human-friendly descriptions for every parameter group
# ---------------------------------------------------------------------------

# Plain-language help for concentration parameters
CONCENTRATION_HELP = {
    "ctc_concentration": "Cytotoxic T-cells — killer immune cells that directly destroy tumor cells",
    "neutrophil_concentration": "Neutrophils — first responders that attack cancer early on",
    "mast_cell_concentration": "Mast cells — release chemicals that attract other immune cells",
    "treg_concentration": "Regulatory T-cells — suppress immune responses (can help tumor survive)",
    "pdc_concentration": "Plasmacytoid dendritic cells — activate NK cells and coordinate immune response",
    "th1_concentration": "Th1 helper cells — boost anti-tumor immunity",
    "th2_concentration": "Th2 helper cells — can reduce anti-tumor response",
    "dc_concentration": "Dendritic cells — present tumor signals to activate other immune cells",
    "m1_concentration": "M1 macrophages — pro-inflammatory, attack tumor cells",
    "m2_concentration": "M2 macrophages — anti-inflammatory, can promote tumor growth",
    "nkl_concentration": "Natural killer cells — innate immune cells that kill tumor on contact",
    "cd4_concentration": "CD4 T-cells — helper cells that coordinate immune attacks",
    "cd8_concentration": "CD8 T-cells — cytotoxic cells that kill infected/cancer cells",
}

# Plain-language help for glucose parameters
GLUCOSE_HELP = {
    "w_glucose_diffusion": "How fast glucose spreads through tissue (higher = more even distribution)",
    "w_glucose_decay": "How fast glucose naturally breaks down (higher = less available)",
    "w_glucose_source_rate": "How much glucose blood vessels supply (higher = more energy available)",
    "w_glucose_tumor_consumption": "How much glucose tumor cells consume (tumors are hungry — Warburg effect)",
    "w_glucose_immune_consumption": "How much glucose immune cells consume (they need energy to fight)",
    "w_glucose_growth_sensitivity": "How much glucose levels affect tumor growth rate",
    "w_glucose_immune_sensitivity": "How much glucose levels affect immune cell effectiveness",
    "w_glucose_chemotaxis_strength": "How strongly immune cells move toward glucose-rich areas",
}

# Plain-language group descriptions for advanced weights
WEIGHT_GROUP_DESCRIPTIONS = {
    "BMI Effects": "How the patient's body weight affects immune cell behavior. Higher BMI generally weakens anti-tumor responses.",
    "Tumor": "Controls tumor cell behavior — growth, death, blood vessel formation, and immune evasion.",
    "M1 Macrophage": "M1 macrophages are pro-inflammatory — they attack tumors. These control their strength and behavior.",
    "M2 Macrophage": "M2 macrophages are anti-inflammatory — they can promote tumor growth. These control their effects.",
    "CD4 T Cell": "CD4 helper T-cells coordinate the immune response. These control how they differentiate and activate other cells.",
    "Cytotoxic T Cell (CD8)": "CD8 T-cells are the main tumor killers. These control their movement, killing power, and exhaustion.",
    "Natural Killer": "NK cells kill tumor cells on contact without prior activation. These control their kill rate.",
    "DC / PDC": "Dendritic cells detect tumor signals and activate other immune cells. These control their effectiveness.",
    "Treg": "Regulatory T-cells suppress immune responses. These control how much they inhibit anti-tumor immunity.",
    "Mast Cell": "Mast cells release inflammatory signals. These control their effects on tumors and other immune cells.",
    "Neutrophil": "Neutrophils are early responders. These control their tumor-killing ability.",
    "Adipocyte": "Fat cells in the tissue. These control how they influence tumor growth and macrophage behavior.",
    "General": "General simulation parameters — search radius, drug effectiveness, cell death rates.",
}

# Plain-language help for individual advanced weight parameters
WEIGHT_HELP = {
    "w_BMI_on_treg_diff": "How much obesity increases Treg (immune-suppressing) cells",
    "w_BMI_on_m1_mutation": "How much obesity affects pro-inflammatory macrophages",
    "w_BMI_on_m2_mutation": "How much obesity boosts tumor-promoting macrophages",
    "w_BMI_nkl_kill_rate": "How much obesity reduces NK cell killing power",
    "w_tumor_apoptosis_eff": "How effectively the immune system triggers tumor cell death",
    "w_tumor_apoptosis_dna": "How DNA damage contributes to tumor cell death",
    "b_tumor_apoptosis": "Baseline tumor cell death rate (higher = easier to kill)",
    "w_tumor_growth_eff": "How fast tumor cells multiply",
    "w_tumor_growth_dna": "How DNA mutations affect tumor growth speed",
    "b_tumor_growth": "Baseline tumor growth rate",
    "w_tumor_angiogenesis": "How fast tumors grow new blood vessels",
    "b_tumor_angiogenesis": "Baseline blood vessel formation rate",
    "w_antigen_presentation": "How visible tumors are to the immune system",
    "b_antigen_presentation": "Baseline tumor visibility",
    "w_angiogenesis_tumor_growth": "How much new blood vessels help tumor growth",
    "w_gene_pd1_inhibition": "How much PD-1 (immune checkpoint) shields tumors from attack",
    "w_tumour_growth_threshold": "Tumor size at which terminal condition triggers",
    "w_m1_mutation": "How easily M1 macrophages activate",
    "b_m1_mutation": "Baseline M1 activation threshold",
    "w_m1_move": "How far M1 macrophages can move to find tumors",
    "w_m1_phagocytosis": "How effectively M1 macrophages eat tumor cells",
    "w_m1_digest": "How fast M1 macrophages digest eaten cells",
    "w_m1_t_kill_rate": "How much M1 macrophages help T-cells kill",
    "w_m1_th1_proliferation": "How much M1 cells stimulate Th1 helper cells",
    "w_th1_proliferation": "Th1 cell multiplication rate",
    "b_th1_proliferation": "Baseline Th1 proliferation threshold",
    "w_m2_mutation": "How easily M2 macrophages activate",
    "b_m2_mutation": "Baseline M2 activation threshold",
    "w_m2_move": "How far M2 macrophages can move",
    "w_m2_t_kill_rate": "How much M2 macrophages suppress T-cell killing",
    "w_m2_tumour_growth": "How much M2 macrophages help tumors grow",
    "w_m2_angiogenesis": "How much M2 macrophages promote blood vessel formation",
    "w_cd4_treg_diff_effect": "How strongly CD4 cells differentiate into Tregs (suppressive)",
    "w_cd4_treg_diff_horm": "Hormonal influence on CD4→Treg conversion",
    "b_cd4_treg_diff": "Baseline CD4→Treg conversion rate",
    "w_cd4_th1_proliferation_effect": "How strongly CD4 cells activate Th1 helpers",
    "w_cd4_th1_proliferation_horm": "Hormonal influence on CD4→Th1 activation",
    "b_cd4_th1_proliferation": "Baseline CD4→Th1 activation rate",
    "w_cd4_th1_spawn_m1": "How many M1 macrophages Th1 cells recruit",
    "w_cd4_th1_spawn_dc": "How many dendritic cells Th1 cells recruit",
    "w_cd4_th2_spawn_m1": "Th2 effect on M1 macrophage recruitment",
    "w_cd4_th2_spawn_t": "Th2 effect on T-cell recruitment",
    "w_cd4_th2_proliferation_effect": "How strongly CD4 cells activate Th2 helpers",
    "w_cd4_th2_proliferation_horm": "Hormonal influence on CD4→Th2 activation",
    "b_cd4_th2_proliferation": "Baseline CD4→Th2 activation rate",
    "w_cytotoxic_move": "How far cytotoxic T-cells move to find tumors",
    "w_cytotoxic_proliferation": "How fast cytotoxic T-cells multiply",
    "w_cytotoxic_apoptosis": "How easily cytotoxic T-cells die (exhaustion)",
    "b_cytotoxic_apoptosis": "Baseline cytotoxic T-cell death rate",
    "w_cytotoxic_kill": "How effectively cytotoxic T-cells kill tumor cells",
    "b_cytotoxic_kill": "Baseline cytotoxic T-cell kill chance",
    "w_cytotoxic_pd1_inhibition": "How much PD-1 checkpoint reduces T-cell killing (ICI blocks this)",
    "w_sex_hormone_cd8": "How sex hormones affect CD8 T-cell behavior",
    "w_natural_killer_kill_rate": "NK cell killing power",
    "b_natural_killer_kill_rate": "Baseline NK kill chance",
    "w_nkl_t_kill_rate": "How much NK cells boost T-cell killing",
    "w_dc_phagocytosis_effect": "How effectively dendritic cells detect tumor cells",
    "b_dc_phagocytosis": "Baseline dendritic cell detection rate",
    "w_pdc_nkl_spawn": "How many NK cells plasmacytoid DCs recruit",
    "b_pdc_nkl_spawn": "Baseline PDC→NK recruitment rate",
    "w_pdc_angiogenesis": "PDC effect on blood vessel formation",
    "w_pdc_treg_diff": "PDC influence on Treg differentiation",
    "w_pdc_t_proliferation": "PDC effect on T-cell multiplication",
    "w_pdc_t_kill": "PDC effect on T-cell killing power",
    "w_pdc_nkl_kill": "PDC effect on NK cell killing power",
    "w_treg_move": "How far Tregs move",
    "w_treg_t_kill_rate": "How much Tregs suppress T-cell killing",
    "w_treg_t_proliferation": "How much Tregs suppress T-cell multiplication",
    "w_treg_t_apoptosis": "How much Tregs cause T-cell death",
    "w_treg_activation": "How easily Tregs become active",
    "w_treg_dc_phagocytosis": "How much Tregs reduce dendritic cell activity",
    "w_mast_cell_angiogenesis": "How much mast cells promote blood vessel growth",
    "w_mast_cell_m1_mutation": "How much mast cells activate M1 macrophages",
    "w_mast_cell_t_kill_rate": "How much mast cells boost T-cell killing",
    "w_mast_cell_tumour_apoptosis": "How much mast cells promote tumor death",
    "w_mast_cell_tumour_growth": "How much mast cells affect tumor growth",
    "w_mast_cell_spawn_dc": "How many dendritic cells mast cells recruit",
    "w_neutrophil_kill_rate": "Neutrophil tumor-killing power",
    "b_neutrophil_kill_rate": "Baseline neutrophil kill chance",
    "w_adipocyte_tumour_growth": "How much fat cells promote tumor growth",
    "w_adipocyte_m2_mutation": "How much fat cells promote M2 (tumor-friendly) macrophages",
    "w_search_dimension": "How far cells can look for neighbors (search radius)",
    "w_ici_effectiveness": "How effective immunotherapy (ICI) is at blocking immune checkpoints",
    "w_tki_effectiveness": "How effective targeted therapy (TKI) is at blocking tumor signals",
    "w_cell_base_death_prob": "Natural cell death probability per step",
    "w_progressive_exhaustion": "How quickly immune cells become exhausted over time",
    "receptor_threshold_variation": "Random variation in cell receptor sensitivity",
    "w_max_drift": "Maximum random movement per step",
    "w_hormone_decay_rate": "How fast sex hormones decay in the tissue",
    "w_hormone_perception_cap": "Maximum hormone level a cell can perceive",
    "neutrophil_max_lifespan": "Maximum number of steps a neutrophil survives",
    "w_cd4_th1_ratio": "Ratio controlling CD4 differentiation toward Th1 vs Th2",
}

# ---------------------------------------------------------------------------
# Weight parameter groupings for the Advanced section
# ---------------------------------------------------------------------------

WEIGHT_GROUPS = {
    "BMI Effects": [
        "w_BMI_on_treg_diff", "w_BMI_on_m1_mutation",
        "w_BMI_on_m2_mutation", "w_BMI_nkl_kill_rate",
    ],
    "Tumor": [
        "w_tumor_apoptosis_eff", "w_tumor_apoptosis_dna", "b_tumor_apoptosis",
        "w_tumor_growth_eff", "w_tumor_growth_dna", "b_tumor_growth",
        "w_tumor_angiogenesis", "b_tumor_angiogenesis",
        "w_antigen_presentation", "b_antigen_presentation",
        "w_angiogenesis_tumor_growth", "w_gene_pd1_inhibition",
        "w_tumour_growth_threshold",
    ],
    "M1 Macrophage": [
        "w_m1_mutation", "b_m1_mutation", "w_m1_move",
        "w_m1_phagocytosis", "w_m1_digest",
        "w_m1_t_kill_rate", "w_m1_th1_proliferation",
        "w_th1_proliferation", "b_th1_proliferation",
    ],
    "M2 Macrophage": [
        "w_m2_mutation", "b_m2_mutation", "w_m2_move",
        "w_m2_t_kill_rate", "w_m2_tumour_growth", "w_m2_angiogenesis",
    ],
    "CD4 T Cell": [
        "w_cd4_treg_diff_effect", "w_cd4_treg_diff_horm", "b_cd4_treg_diff",
        "w_cd4_th1_proliferation_effect", "w_cd4_th1_proliferation_horm",
        "b_cd4_th1_proliferation",
        "w_cd4_th1_spawn_m1", "w_cd4_th1_spawn_dc",
        "w_cd4_th2_spawn_m1", "w_cd4_th2_spawn_t",
        "w_cd4_th2_proliferation_effect", "w_cd4_th2_proliferation_horm",
        "b_cd4_th2_proliferation",
        "w_cd4_th1_ratio",
    ],
    "Cytotoxic T Cell (CD8)": [
        "w_cytotoxic_move", "w_cytotoxic_proliferation",
        "w_cytotoxic_apoptosis", "b_cytotoxic_apoptosis",
        "w_cytotoxic_kill", "b_cytotoxic_kill",
        "w_cytotoxic_pd1_inhibition", "w_sex_hormone_cd8",
    ],
    "Natural Killer": [
        "w_natural_killer_kill_rate", "b_natural_killer_kill_rate",
        "w_nkl_t_kill_rate",
    ],
    "DC / PDC": [
        "w_dc_phagocytosis_effect", "b_dc_phagocytosis",
        "w_pdc_nkl_spawn", "b_pdc_nkl_spawn",
        "w_pdc_angiogenesis", "w_pdc_treg_diff",
        "w_pdc_t_proliferation", "w_pdc_t_kill", "w_pdc_nkl_kill",
    ],
    "Treg": [
        "w_treg_move", "w_treg_t_kill_rate", "w_treg_t_proliferation",
        "w_treg_t_apoptosis", "w_treg_activation", "w_treg_dc_phagocytosis",
    ],
    "Mast Cell": [
        "w_mast_cell_angiogenesis", "w_mast_cell_m1_mutation",
        "w_mast_cell_t_kill_rate", "w_mast_cell_tumour_apoptosis",
        "w_mast_cell_tumour_growth", "w_mast_cell_spawn_dc",
    ],
    "Neutrophil": [
        "w_neutrophil_kill_rate", "b_neutrophil_kill_rate",
        "neutrophil_max_lifespan",
    ],
    "Adipocyte": [
        "w_adipocyte_tumour_growth", "w_adipocyte_m2_mutation",
    ],
    "General": [
        "w_search_dimension", "w_ici_effectiveness", "w_tki_effectiveness",
        "w_cell_base_death_prob", "w_progressive_exhaustion",
        "receptor_threshold_variation", "w_max_drift",
        "w_hormone_decay_rate", "w_hormone_perception_cap",
    ],
}

CONCENTRATION_KEYS = [
    "ctc_concentration", "neutrophil_concentration", "mast_cell_concentration",
    "treg_concentration", "pdc_concentration", "th1_concentration",
    "th2_concentration", "dc_concentration", "m1_concentration",
    "m2_concentration", "nkl_concentration", "cd4_concentration",
    "cd8_concentration",
]

GLUCOSE_KEYS = [
    "w_glucose_diffusion", "w_glucose_decay", "w_glucose_source_rate",
    "w_glucose_tumor_consumption", "w_glucose_immune_consumption",
    "w_glucose_growth_sensitivity", "w_glucose_immune_sensitivity",
    "w_glucose_chemotaxis_strength",
]

BMI_CATEGORIES = [
    (0, 18.5, "Underweight", "#3B82F6"),
    (18.5, 25, "Normal", "#22C55E"),
    (25, 30, "Overweight", "#F59E0B"),
    (30, 35, "Obese I", "#EF4444"),
    (35, 40, "Obese II", "#DC2626"),
    (40, 100, "Obese III", "#991B1B"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bmi_category(bmi: float) -> tuple[str, str]:
    """Return (category_name, hex_color) for the given BMI value."""
    for lo, hi, name, color in BMI_CATEGORIES:
        if lo <= bmi < hi:
            return name, color
    return "Unknown", "#94A3B8"


def _param_bounds(key: str):
    """Return (min_value, max_value) for a parameter, or (None, None) if unconstrained."""
    # Concentration parameters: non-negative integers
    if key.endswith("_concentration"):
        return (0, None)
    # Kill rates, probabilities, effectiveness: 0-1 range floats
    if any(key.startswith(p) for p in ("w_", "b_")) and any(
        t in key for t in ("kill", "apoptosis", "effectiveness", "death_prob")
    ):
        return (0.0, None)
    # Lifespan parameters: positive integers
    if "lifespan" in key:
        return (1, None)
    # Glucose params: non-negative
    if "glucose" in key:
        return (0.0, None)
    return (None, None)


def _widget_for_param(key: str, value, labels: dict, steps: dict,
                      prefix: str = "", help_text: str = ""):
    """Render appropriate widget for a parameter, return new value."""
    label = labels.get(key, format_column_name(key))
    wkey = f"{prefix}_{key}"
    min_val, max_val = _param_bounds(key)

    if isinstance(value, bool):
        return st.checkbox(label, value=value, key=wkey, help=help_text or None)
    elif isinstance(value, int):
        step = steps.get(key, 1)
        kwargs = {}
        if min_val is not None:
            kwargs["min_value"] = int(min_val)
        if max_val is not None:
            kwargs["max_value"] = int(max_val)
        return st.number_input(label, value=value, step=step, key=wkey,
                               help=help_text or None, **kwargs)
    elif isinstance(value, float):
        step = steps.get(key, 0.01)
        fmt = "%.6f" if step < 0.001 else ("%.4f" if step < 0.01 else "%.2f")
        kwargs = {}
        if min_val is not None:
            kwargs["min_value"] = float(min_val)
        if max_val is not None:
            kwargs["max_value"] = float(max_val)
        return st.number_input(label, value=value, step=step, format=fmt,
                               key=wkey, help=help_text or None, **kwargs)
    elif isinstance(value, str):
        return st.text_input(label, value=value, key=wkey, help=help_text or None)
    else:
        return st.text_input(label, value=str(value), key=wkey, help=help_text or None)


def render_param_group(keys: list[str], params: dict, labels: dict, steps: dict,
                       columns: int = 1, prefix: str = "",
                       help_dict: dict | None = None):
    """Render a group of parameter widgets. Returns updated params subset."""
    updated = {}
    if columns > 1:
        cols = st.columns(columns)
        for i, key in enumerate(keys):
            if key not in params:
                continue
            with cols[i % columns]:
                help_text = (help_dict or {}).get(key, "")
                updated[key] = _widget_for_param(key, params[key], labels, steps,
                                                 prefix, help_text)
    else:
        for key in keys:
            if key not in params:
                continue
            help_text = (help_dict or {}).get(key, "")
            updated[key] = _widget_for_param(key, params[key], labels, steps,
                                             prefix, help_text)
    return updated


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.title("Set Up Your Simulation")
st.caption("Choose a patient, pick a treatment, and configure the simulation. "
           "Start with a preset scenario or customize everything yourself.")

defaults = load_all_defaults()
labels = load_all_labels()
steps = load_all_steps()
optimized = load_optimized_preset()
scenarios = load_scenario_presets()

# Initialize params in session state
if "params" not in st.session_state:
    st.session_state["params"] = dict(defaults)

params = st.session_state["params"]

# --- Preset selector ---
st.subheader("Quick Start")
st.caption("Pick a scenario to jump in, or scroll down to customize everything.")

_SCENARIO_NAMES = list(scenarios.keys())

_OUTCOME_CSS = {
    "SURVIVAL": "outcome-survival",
    "PROGRESSION": "outcome-progression",
    "STABLE": "outcome-stable",
    "VARIABLE": "outcome-variable",
}
_OUTCOME_LABELS = {
    "SURVIVAL": "Likely: Tumor eliminated",
    "PROGRESSION": "Likely: Tumor grows",
    "STABLE": "Likely: Balanced",
    "VARIABLE": "Outcome varies",
}

_current_preset = st.session_state.get("preset_selector", "Default")

if _SCENARIO_NAMES:
    # Interactive scenario cards with buttons
    scenario_cols = st.columns(min(4, len(_SCENARIO_NAMES)))
    for i, name in enumerate(_SCENARIO_NAMES):
        sc = scenarios[name]
        hint = sc["outcome_hint"]
        css_cls = _OUTCOME_CSS.get(hint, "outcome-variable")
        label = _OUTCOME_LABELS.get(hint, hint)
        is_active = (_current_preset == name)
        active_cls = " active" if is_active else ""
        with scenario_cols[i % len(scenario_cols)]:
            st.markdown(
                f'<div class="scenario-card{active_cls}" role="group" aria-label="Scenario: {name}">'
                f'<h5>{name}</h5>'
                f'<p>{sc["description"]}</p>'
                f'<span class="outcome-hint {css_cls}" role="status" aria-label="{label}">{label}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(
                "Selected" if is_active else "Use This",
                key=f"sc_btn_{i}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                disabled=is_active,
            ):
                st.session_state["preset_selector"] = name
                base = dict(defaults)
                base.update(sc["overrides"])
                params.update(base)
                st.session_state["params"] = params
                st.rerun()

st.markdown("")

# Base preset row (Default / Optimized / Custom)
with st.expander("Or choose a base preset", expanded=_current_preset in ("Default", "Optimized", "Custom"),
                 icon=":material/tune:"):
    _BASE_PRESETS = ["Default", "Optimized", "Custom"]
    preset = st.segmented_control(
        "Base preset", _BASE_PRESETS,
        default=_current_preset if _current_preset in _BASE_PRESETS else None,
        key="base_preset_ctrl",
        help="Default = standard values. Optimized = calibrated for realism. Custom = keep current.",
    )
    if preset:
        st.session_state["preset_selector"] = preset
        if preset == "Default":
            st.caption("Standard starting values — good for exploring the simulator.")
            params.update(dict(defaults))
        elif preset == "Optimized":
            st.caption("Calibrated parameters for more realistic simulations.")
            base = dict(defaults)
            base.update(optimized)
            params.update(base)
        elif preset == "Custom":
            st.caption("Keep current values and edit any parameter below.")

# Apply scenario preset if selected (and not already applied via button click)
if _current_preset in scenarios and _current_preset == st.session_state.get("preset_selector"):
    pass  # Already applied above or on a previous rerun

# =========================================================================
# SECTION 1: Patient Profile
# =========================================================================

st.header("👤 Patient Profile")
st.caption("Who is the virtual patient? These biological characteristics significantly affect how the immune system responds to cancer.")

pc1, pc2 = st.columns(2)
with pc1:
    params["sex"] = st.segmented_control(
        "Biological Sex", ["F", "M"],
        default=params["sex"],
        key="cfg_sex",
        format_func=lambda s: "Female" if s == "F" else "Male",
        help="Sex affects hormone levels, which influence immune cell behavior.",
    )
    if params["sex"] is None:
        params["sex"] = "F"
    sex_note = ("Estrogen can enhance T-cell responses and anti-tumor immunity."
                if params["sex"] == "F"
                else "Testosterone may slightly reduce some immune responses.")
    st.caption(f"**{format_sex(params['sex'])}** — {sex_note}")

with pc2:
    params["BMI"] = st.slider(
        "Body Mass Index (BMI)", min_value=15.0, max_value=50.0,
        value=float(params["BMI"]), step=0.5, key="cfg_bmi",
        help="BMI affects the tumor microenvironment. Higher BMI increases "
             "regulatory T-cells and tumor-friendly macrophages, making it harder "
             "for the immune system to fight cancer.",
    )

# BMI visual feedback
bmi_cat, bmi_color = _bmi_category(params["BMI"])
bmi_effects = {
    "Underweight": "Minimal effect on immune dynamics.",
    "Normal": "Balanced immune environment — best conditions for treatment.",
    "Overweight": "Slight increase in immune-suppressing cells.",
    "Obese I": "Noticeable increase in Tregs and M2 macrophages. Reduced NK killing.",
    "Obese II": "Strong immune suppression. Treatment may be less effective.",
    "Obese III": "Severe immune suppression. Very challenging treatment conditions.",
}
st.markdown(
    f"<strong style='color:{bmi_color}'>{bmi_cat}</strong> — {bmi_effects.get(bmi_cat, '')}",
    unsafe_allow_html=True,
)

if params["BMI"] >= 30:
    st.warning(
        "**High BMI effect:** Increases immune-suppressing cells (Tregs, M2 macrophages) "
        "and reduces NK cell killing power. Treatment may be less effective.",
        icon=":material/warning:",
    )

st.markdown("")

# =========================================================================
# SECTION 2: Treatment Strategy
# =========================================================================

st.header("💊 Treatment Strategy")
st.caption("Choose your therapeutic approach. Treatment begins after an initial tumor establishment phase, simulating real clinical timing.")

# Visual treatment cards
_TREATMENT_CARDS = [
    ("None", "No Treatment", "Control run — natural immunity only",
     "&#x1F50D;"),
    ("ICI", "Immunotherapy", "Removes brakes on immune cells (PD-1/PD-L1)",
     "&#x1F6E1;&#xFE0F;"),
    ("TKI", "Targeted Therapy", "Cuts off tumor blood supply",
     "&#x1F6AB;"),
    ("ICI+TKI", "Combination", "Both approaches — strongest option",
     "&#x2694;&#xFE0F;"),
]

tc_cols = st.columns(4)
for i, (trt_key, trt_name, trt_desc, trt_icon) in enumerate(_TREATMENT_CARDS):
    with tc_cols[i]:
        sel_cls = " selected" if params["treatment"] == trt_key else ""
        st.markdown(
            f'<div class="treatment-card{sel_cls}" role="group" aria-label="Treatment option: {trt_name}">'
            f'<div class="tc-icon" aria-hidden="true">{trt_icon}</div>'
            f'<div class="tc-name">{trt_name}</div>'
            f'<div class="tc-desc">{trt_desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "Selected" if params["treatment"] == trt_key else "Select",
            key=f"trt_card_{trt_key}",
            use_container_width=True,
            type="primary" if params["treatment"] == trt_key else "secondary",
            disabled=params["treatment"] == trt_key,
        ):
            params["treatment"] = trt_key
            st.session_state["params"] = params
            st.rerun()

st.markdown("")

# Treatment start timing
params["treatment_start"] = st.slider(
    "Start treatment at step",
    min_value=0, max_value=max(200, params.get("max_steps", 200)),
    value=params["treatment_start"],
    step=5, key="cfg_tstart",
    help="The simulation first runs without treatment to establish the tumor. "
         "Treatment begins at this step. Lower = earlier intervention.",
    disabled=params["treatment"] == "None",
)
if params["treatment"] != "None":
    if params["treatment_start"] == 0:
        st.caption("Treatment starts immediately — no observation period.")
    elif params["treatment_start"] <= 20:
        st.caption(f"Early intervention — treatment begins at step {params['treatment_start']}.")
    elif params["treatment_start"] >= 80:
        st.caption(f"Late intervention — tumor has {params['treatment_start']} steps to grow before treatment.")
    else:
        st.caption(f"Treatment begins at step {params['treatment_start']}.")

# Treatment impact preview
_TREATMENT_IMPACT = {
    "None": "No drugs will be applied. The tumor grows with only natural immune defense. "
            "Useful as a baseline to compare against treatment runs.",
    "ICI": "Immunotherapy blocks PD-1/PD-L1 checkpoints, letting T-cells attack the tumor again. "
           "Most effective when the immune system is already present but suppressed.",
    "TKI": "Targeted therapy blocks signals tumors use to grow blood vessels (angiogenesis). "
           "Starves the tumor of glucose. Works best against fast-growing tumors.",
    "ICI+TKI": "Combination therapy attacks from both sides — boosting immunity AND cutting off tumor supply. "
               "Most powerful option, but the simulation still depends on timing and patient factors.",
}
impact_text = _TREATMENT_IMPACT.get(params["treatment"], "")
if impact_text:
    with st.container(border=True):
        st.markdown(
            f"{treatment_badge_html(params['treatment'])} "
            f"starting at step **{params['treatment_start']}**",
            unsafe_allow_html=True,
        )
        st.caption(impact_text)

# =========================================================================
# SECTION 3: Simulation Settings
# =========================================================================

st.header("⚙️ Simulation Settings")
st.caption("Configure the computational parameters: duration, tissue size, and randomness seed.")

col1, col2, col3 = st.columns(3)
with col1:
    params["max_steps"] = st.number_input(
        "Duration (steps)", value=params["max_steps"],
        step=10, min_value=1, key="cfg_maxsteps",
        help="Each step simulates one time unit. More steps = longer simulation. "
             "The simulation may end early if the tumor is eliminated or grows too large.",
    )
with col2:
    # Tissue size as a friendlier selection
    _VOLUME_PRESETS = {
        "Tiny (fast)": 0.000001,
        "Small": 0.000004,
        "Medium": 0.000008,
        "Large (slow)": 0.000015,
    }
    # Find closest preset
    _current_vol = params["volume"]
    _closest_name = min(_VOLUME_PRESETS, key=lambda k: abs(_VOLUME_PRESETS[k] - _current_vol))
    vol_choice = st.selectbox(
        "Tissue Size", list(_VOLUME_PRESETS.keys()),
        index=list(_VOLUME_PRESETS.keys()).index(_closest_name),
        key="cfg_volume_preset",
        help="Larger tissue means more cells and a bigger 3D grid, but takes longer to simulate.",
    )
    params["volume"] = _VOLUME_PRESETS[vol_choice]
with col3:
    params["random_seed"] = st.number_input(
        "Random Seed", value=params["random_seed"],
        step=1, key="cfg_seed",
        help="Controls randomness. Same seed = same results. "
             "Change the seed to see how random variation affects the outcome.",
    )

dim = get_dimension_from_volume(params["volume"], params.get("block_size", 10))
st.caption(f":material/grid_on: Creates a **{dim}\u00d7{dim}\u00d7{dim}** grid ({dim**3:,} voxels) of tissue")

# =========================================================================
# SECTION 4: Immune Cell Concentrations
# =========================================================================

with st.expander("Immune Cell Populations", expanded=False, icon=":material/bloodtype:"):
    st.markdown("""
    **How many of each immune cell type start in the tissue?**

    Higher concentrations mean a stronger initial immune response.
    Hover over the **?** icon next to each parameter for a description of what that cell type does.
    Default values shown below for reference.
    """)
    # Show reference ranges
    _conc_defaults = {k: defaults.get(k) for k in CONCENTRATION_KEYS if k in defaults}
    if _conc_defaults:
        _ref_parts = [f"**{labels.get(k, k)}:** {v:,}" for k, v in _conc_defaults.items() if v is not None]
        st.caption("Default values: " + " · ".join(_ref_parts))
    conc_updates = render_param_group(
        CONCENTRATION_KEYS, params, labels, steps,
        columns=3, prefix="conc", help_dict=CONCENTRATION_HELP)
    params.update(conc_updates)

# =========================================================================
# SECTION 5: Glucose
# =========================================================================

with st.expander("Glucose & Energy", expanded=False, icon=":material/water_drop:"):
    st.markdown("""
    **Glucose is the energy source for all cells.**

    Tumor cells consume glucose at a very high rate (the "Warburg effect").
    When glucose runs low, immune cells become less effective.
    These parameters control glucose supply, consumption, and how cells respond to it.
    """)
    gluc_updates = render_param_group(
        GLUCOSE_KEYS, params, labels, steps,
        columns=2, prefix="gluc", help_dict=GLUCOSE_HELP)
    params.update(gluc_updates)

# =========================================================================
# SECTION 6: Advanced Weights
# =========================================================================

with st.expander("Advanced: Cell Interaction Weights", expanded=False, icon=":material/tune:"):
    st.markdown("""
    **Fine-grained control over cell behavior and interactions.**

    These parameters are the "knobs" of the simulation model. Each one controls
    a specific biological interaction. Only change these if you want to explore
    specific hypotheses. Hover over **?** for plain-language descriptions.
    """)

    # Parameter search
    _adv_search = st.text_input(
        "Search parameters",
        placeholder="e.g. PD-1, kill rate, angiogenesis...",
        key="adv_param_search",
        help="Filter parameters by name or description.",
    )

    # Show changes from default toggle
    _show_changed = st.toggle(
        "Show only changed parameters",
        value=False,
        key="adv_show_changed",
        help="Highlight parameters that differ from default values.",
    )

    for group_name, group_keys in WEIGHT_GROUPS.items():
        desc = WEIGHT_GROUP_DESCRIPTIONS.get(group_name, "")

        # Apply search filter
        if _adv_search:
            search_lower = _adv_search.lower()
            filtered_keys = [
                k for k in group_keys
                if search_lower in k.lower()
                or search_lower in labels.get(k, "").lower()
                or search_lower in WEIGHT_HELP.get(k, "").lower()
            ]
        else:
            filtered_keys = group_keys

        # Apply show-changed filter
        if _show_changed:
            filtered_keys = [
                k for k in filtered_keys
                if k in params and params[k] != defaults.get(k)
            ]

        if not filtered_keys:
            continue

        n_changed = sum(1 for k in group_keys if k in params and params[k] != defaults.get(k))
        changed_label = f" — {n_changed} changed" if n_changed > 0 else ""
        with st.expander(f"{group_name} ({len(filtered_keys)} parameters{changed_label})", expanded=bool(_adv_search)):
            if desc:
                st.caption(desc)
            # Show which params differ from defaults
            if n_changed > 0 and not _show_changed:
                changed_names = [
                    labels.get(k, k) for k in group_keys
                    if k in params and params[k] != defaults.get(k)
                ]
                st.caption(f"Changed: {', '.join(changed_names)}")
            wt_updates = render_param_group(
                filtered_keys, params, labels, steps,
                columns=3, prefix=f"wt_{group_name[:4]}",
                help_dict=WEIGHT_HELP)
            params.update(wt_updates)

# Store back
st.session_state["params"] = params

# =========================================================================
# Setup Summary & Actions
# =========================================================================

st.divider()

# --- Your Setup summary ---
_sex_label = "Female" if params["sex"] == "F" else "Male"
_bmi_cat, _bmi_col = _bmi_category(params["BMI"])
_trt = TREATMENT_LABELS.get(params["treatment"], params["treatment"])

# Quick assessment
_notes = []
if params["treatment"] == "None":
    _notes.append("No treatment — tumor relies on natural immunity only")
elif params["treatment"] == "ICI+TKI":
    _notes.append("Strongest treatment option")
if params["BMI"] >= 30:
    _notes.append("High BMI may weaken immune response")
if params["treatment_start"] > 50:
    _notes.append("Late treatment start — tumor has time to grow")
elif params["treatment_start"] < 10 and params["treatment"] != "None":
    _notes.append("Early treatment — quick intervention")

with st.container(border=True):
    st.subheader("Your Setup", anchor=False)
    sc1, sc2, sc3 = st.columns(3)
    sc1.markdown(f"**Patient:** {_sex_label}, BMI {params['BMI']:.1f} "
                 f"(<span style='color:{_bmi_col}'>{_bmi_cat}</span>)",
                 unsafe_allow_html=True)
    sc2.markdown(f"**Treatment:** {_trt}")
    sc3.markdown(f"**Duration:** {params['max_steps']} steps, "
                 f"treatment at step {params['treatment_start']}")
    if _notes:
        st.caption(" · ".join(_notes))

st.markdown("")

# --- Action buttons ---
if st.button(":material/play_arrow: Run Simulation", type="primary", use_container_width=True):
    st.switch_page("pages/2_run.py")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button(":material/restart_alt: Reset to Defaults", type="secondary", use_container_width=True):
        st.session_state["params"] = dict(defaults)
        st.rerun()
with col2:
    yaml_str = params_to_yaml(params)
    st.download_button(
        ":material/download: Export Config",
        data=yaml_str,
        file_name="rcc_config.yaml",
        mime="text/yaml",
        use_container_width=True,
    )
with col3:
    uploaded = st.file_uploader(
        "Import Config",
        type=["yaml", "yml"],
        key="cfg_import",
        label_visibility="collapsed",
        help="Load a previously exported YAML configuration file.",
    )
    if uploaded is not None:
        try:
            imported = yaml_to_params(uploaded.read().decode("utf-8"))
            base = dict(defaults)
            base.update(imported)
            st.session_state["params"] = base
            st.session_state["preset_selector"] = "Custom"
            st.success("Configuration imported successfully.")
            # Clear the uploader before rerun to prevent infinite loop
            st.session_state["cfg_import"] = None
            st.rerun()
        except Exception as e:
            st.error(f"Failed to import config: {e}")

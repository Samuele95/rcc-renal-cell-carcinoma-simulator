from dataclasses import dataclass
from src.parameters.parameters import Parameters


@dataclass
class WeightParameters(Parameters):
    # BMI weights
    w_BMI_on_treg_diff: float = 0.01
    w_BMI_on_m1_mutation: float = 0.01
    w_BMI_on_m2_mutation: float = 0.01
    w_BMI_nkl_kill_rate: float = 0.01

    w_treg_move: float = 1
    w_cytotoxic_move: float = 1

    w_m1_mutation: float = 1
    b_m1_mutation: float = 0
    w_m1_move: float = 1
    w_m1_phagocytosis: float = 1
    w_m1_digest: float = 1
    w_m1_t_kill_rate: float = 1
    w_m1_th1_proliferation: float = 1
    w_th1_proliferation: float = 1
    b_th1_proliferation: float = 0
    w_dc_phagocytosis_effect: float = 1
    b_dc_phagocytosis: float = 0

    w_m2_mutation: float = 1
    b_m2_mutation: float = 0
    w_m2_move: float = 1
    w_m2_t_kill_rate: float = 1
    w_m2_tumour_growth: float = 1
    w_m2_angiogenesis: float = 1

    w_sex_hormone_cd8: float = 1.0
    w_tumor_apoptosis_eff: float = 1
    w_tumor_apoptosis_dna: float = 1
    b_tumor_apoptosis: float = 0
    w_tumor_growth_eff: float = 0.6
    w_tumor_growth_dna: float = 1
    b_tumor_growth: float = 0
    w_tumor_angiogenesis: float = 1
    b_tumor_angiogenesis: float = 0
    w_antigen_presentation: float = 1
    b_antigen_presentation: float = 0
    w_angiogenesis_tumor_growth: float = 1
    w_gene_pd1_inhibition: float = 1

    w_cd4_treg_diff_effect: float = 1
    w_cd4_treg_diff_horm: float = 1
    b_cd4_treg_diff: float = 0

    w_cd4_th1_proliferation_effect: float = 1
    w_cd4_th1_proliferation_horm: float = 1
    b_cd4_th1_proliferation: float = 0
    w_cd4_th1_spawn_m1: float = 1
    w_cd4_th1_spawn_dc: float = 1

    w_cd4_th2_spawn_m1: float = 1
    w_cd4_th2_spawn_t: float = 1
    w_cd4_th2_proliferation_effect: float = 1
    w_cd4_th2_proliferation_horm: float = 1
    b_cd4_th2_proliferation: float = 0

    w_cytotoxic_proliferation: float = 1
    w_cytotoxic_apoptosis: float = 1
    b_cytotoxic_apoptosis: float = 0
    w_cytotoxic_kill: float = 1
    b_cytotoxic_kill: float = 0
    w_cytotoxic_pd1_inhibition: float = 1

    w_mast_cell_angiogenesis: float = 1
    w_mast_cell_m1_mutation: float = 1
    w_mast_cell_t_kill_rate: float = 1
    w_mast_cell_tumour_apoptosis: float = 1
    w_mast_cell_tumour_growth: float = 1
    w_mast_cell_spawn_dc: float = 1

    w_natural_killer_kill_rate: float = 1
    b_natural_killer_kill_rate: float = 0
    w_nkl_t_kill_rate: float = 1

    w_pdc_nkl_spawn: float = 1
    b_pdc_nkl_spawn: float = 0
    w_pdc_angiogenesis: float = 1
    w_pdc_treg_diff: float = 1
    w_pdc_t_proliferation: float = 1
    w_pdc_t_kill: float = 1
    w_pdc_nkl_kill: float = 1

    w_treg_t_kill_rate: float = 1
    w_treg_t_proliferation: float = 1
    w_treg_t_apoptosis: float = 1
    w_treg_activation: float = 1
    w_treg_dc_phagocytosis: float = 1

    w_search_dimension: float = 0.5
    w_tumour_growth_threshold: float = 1

    w_ici_effectiveness: float = 1
    w_tki_effectiveness: float = 1
    w_cell_base_death_prob: float = 0.009
    w_progressive_exhaustion: float = 0.05

    receptor_threshold_variation: int = 1

    w_max_drift: float = 0.25

    # === NEW: Glucose parameters ===
    w_glucose_diffusion: float = 0.1
    w_glucose_decay: float = 0.01
    w_glucose_source_rate: float = 5.0
    w_glucose_tumor_consumption: float = 2.0
    w_glucose_immune_consumption: float = 0.5
    w_glucose_growth_sensitivity: float = 1.0
    w_glucose_immune_sensitivity: float = 1.0
    w_glucose_chemotaxis_strength: float = 0.3

    # Neutrophil parameters
    w_neutrophil_kill_rate: float = 1.0
    b_neutrophil_kill_rate: float = 0.0
    # Adipocyte parameters
    w_adipocyte_tumour_growth: float = 1.0
    w_adipocyte_m2_mutation: float = 1.0

    param_labels = {
        "w_BMI_on_treg_diff": "Weight of BMI on Treg Differentiation",
        "w_BMI_on_m1_mutation": "Weight of BMI on M1 Macrophage Mutation",
        "w_BMI_on_m2_mutation": "Weight of BMI on M2 Macrophage Mutation",
        "w_BMI_nkl_kill_rate": "Weight of BMI on NKL Kill Rate",
        "w_treg_move": "Weight of treg for move",
        "w_m1_mutation": "Weight of M1 Macrophage Mutation Threshold",
        "b_m1_mutation": "Bias of M1 Macrophage Mutation Threshold",
        "w_m1_move": "Weight of M1 Macrophage Look-Up Movement Radius",
        "w_m1_phagocytosis": "Weight of M1 Macrophage Phagocytosis Chance",
        "w_m1_digest": "Weight of M1 Macrophage Digestion Rate",
        "w_m1_t_kill_rate": "Weight of M1 Macrophage Effect on T-Kill Rate",
        "w_m1_th1_proliferation": "Weight of M1 Macrophage Effect on Th1 Proliferation",
        "w_th1_proliferation": "Weight of M1 Macrophage Effect on Th1 Proliferation",
        "b_th1_proliferation": "Bias of M1 Macrophage Effect on Th1 Proliferation",
        "w_m2_mutation": "Weight of M2 Macrophage Mutation Threshold",
        "b_m2_mutation": "Bias of M2 Macrophage Mutation Threshold",
        "w_m2_move": "Weight of M2 Macrophage Look-Up Movement Radius",
        "w_m2_t_kill_rate": "Weight of M2 Macrophage Effect on T-Kill Rate",
        "w_m2_tumour_growth": "Weight of M2 Macrophage Effect on Tumour Growth",
        "w_m2_angiogenesis": "Weight of M2 Macrophage Effect on Angiogenesis",
        "w_search_dimension": "Weight of Search Dimension for Agents",
        "w_tumour_growth_threshold": "Weight of Terminal Condition for Tumor Growth Threshold",
        "w_glucose_diffusion": "Glucose Diffusion Coefficient",
        "w_glucose_decay": "Glucose Natural Decay Rate",
        "w_glucose_source_rate": "Glucose Source Injection Rate",
        "w_glucose_tumor_consumption": "Glucose Tumor Consumption Rate (Warburg)",
        "w_glucose_immune_consumption": "Glucose Immune Cell Consumption Rate",
        "w_glucose_growth_sensitivity": "Tumor Growth Sensitivity to Glucose",
        "w_glucose_immune_sensitivity": "Immune Function Sensitivity to Glucose",
        "w_glucose_chemotaxis_strength": "Immune Cell Chemotaxis Strength",
        "w_neutrophil_kill_rate": "Weight of Neutrophil Kill Rate",
        "b_neutrophil_kill_rate": "Bias of Neutrophil Kill Rate",
        "w_adipocyte_tumour_growth": "Weight of Adipocyte Effect on Tumour Growth",
        "w_adipocyte_m2_mutation": "Weight of Adipocyte Effect on M2 Mutation",
    }
    param_steps = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

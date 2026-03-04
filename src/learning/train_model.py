"""Optuna-based parameter optimization for the RCC model.

Adapted from Mesa version. Uses RCCModel with MPI.COMM_SELF for single-rank training.
Adds 8 glucose parameters to the search space.
"""
import csv
import json
import os
from typing import Tuple

import numpy as np
import optuna
import pandas as pd
from matplotlib import pyplot as plt

from mpi4py import MPI
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.model.rcc_model import RCCModel
from src.agents.agent_types import AgentType


def suggest_parameters(trial: optuna.Trial) -> dict:
    params = {}

    # === Positive floats (weights)
    positive_weight_keys = [
        "w_BMI_on_treg_diff", "w_BMI_on_m1_mutation", "w_BMI_on_m2_mutation", "w_BMI_nkl_kill_rate",
        "w_treg_move", "w_cytotoxic_move",
        "w_m1_mutation", "w_m1_move", "w_m1_phagocytosis", "w_m1_digest", "w_m1_t_kill_rate",
        "w_m1_th1_proliferation", "w_th1_proliferation", "w_dc_phagocytosis_effect",
        "w_m2_mutation", "w_m2_move", "w_m2_t_kill_rate", "w_m2_tumour_growth", "w_m2_angiogenesis",
        "w_sex_hormone_cd8", "w_tumor_apoptosis_eff", "w_tumor_apoptosis_dna", "w_tumor_growth_eff",
        "w_tumor_growth_dna", "w_tumor_angiogenesis", "w_antigen_presentation", "w_angiogenesis_tumor_growth",
        "w_gene_pd1_inhibition",
        "w_cd4_treg_diff_effect", "w_cd4_treg_diff_horm",
        "w_cd4_th1_proliferation_effect", "w_cd4_th1_proliferation_horm", "w_cd4_th1_spawn_m1", "w_cd4_th1_spawn_dc",
        "w_cd4_th2_spawn_m1", "w_cd4_th2_spawn_t", "w_cd4_th2_proliferation_effect", "w_cd4_th2_proliferation_horm",
        "w_cytotoxic_proliferation", "w_cytotoxic_apoptosis", "w_cytotoxic_kill", "w_cytotoxic_pd1_inhibition",
        "w_mast_cell_angiogenesis", "w_mast_cell_m1_mutation", "w_mast_cell_t_kill_rate", "w_mast_cell_tumour_apoptosis",
        "w_mast_cell_tumour_growth", "w_mast_cell_spawn_dc", "w_natural_killer_kill_rate", "w_nkl_t_kill_rate",
        "w_pdc_nkl_spawn", "w_pdc_angiogenesis", "w_pdc_treg_diff", "w_pdc_t_proliferation",
        "w_pdc_t_kill", "w_pdc_nkl_kill", "w_treg_t_kill_rate", "w_treg_t_proliferation", "w_treg_t_apoptosis",
        "w_treg_activation", "w_treg_dc_phagocytosis", "w_search_dimension",
    ]

    for key in positive_weight_keys:
        params[key] = trial.suggest_float(key, 0.25, 4.0, log=True)

    # === Biases (can be negative)
    bias_keys = [
        "b_m1_mutation", "b_th1_proliferation", "b_dc_phagocytosis", "b_m2_mutation", "b_tumor_apoptosis",
        "b_tumor_growth", "b_tumor_angiogenesis", "b_antigen_presentation", "b_cd4_treg_diff",
        "b_cd4_th1_proliferation", "b_cd4_th2_proliferation", "b_cytotoxic_apoptosis", "b_cytotoxic_kill",
        "b_natural_killer_kill_rate", "b_pdc_nkl_spawn"
    ]

    for key in bias_keys:
        params[key] = trial.suggest_float(key, -1.0, 1.0)

    # === Special range weights
    params["w_tumour_growth_threshold"] = trial.suggest_float("w_tumour_growth_threshold", 0.75, 0.99)

    # === Floats between 0 and 1
    params["w_ici_effectiveness"] = trial.suggest_float("w_ici_effectiveness", 0.0, 1.0)
    params["w_tki_effectiveness"] = trial.suggest_float("w_tki_effectiveness", 0.0, 1.0)
    params["w_cell_base_death_prob"] = trial.suggest_float("w_cell_base_death_prob", 0.001, 0.1)
    params["w_progressive_exhaustion"] = trial.suggest_float("w_progressive_exhaustion", 0.005, 0.3)

    # === Integer in range [0, 3]
    params["receptor_threshold_variation"] = trial.suggest_int("receptor_threshold_variation", 0, 3)

    # === NEW: Glucose parameters
    params["w_glucose_diffusion"] = trial.suggest_float("w_glucose_diffusion", 0.01, 0.16)  # Must be < 1/6
    params["w_glucose_decay"] = trial.suggest_float("w_glucose_decay", 0.001, 0.1)
    params["w_glucose_source_rate"] = trial.suggest_float("w_glucose_source_rate", 1.0, 20.0)
    params["w_glucose_tumor_consumption"] = trial.suggest_float("w_glucose_tumor_consumption", 0.5, 10.0)
    params["w_glucose_immune_consumption"] = trial.suggest_float("w_glucose_immune_consumption", 0.1, 2.0)
    params["w_glucose_growth_sensitivity"] = trial.suggest_float("w_glucose_growth_sensitivity", 0.1, 5.0)
    params["w_glucose_immune_sensitivity"] = trial.suggest_float("w_glucose_immune_sensitivity", 0.1, 5.0)
    params["w_glucose_chemotaxis_strength"] = trial.suggest_float("w_glucose_chemotaxis_strength", 0.05, 0.8)

    return params


HIGH_PENALTY = 500
N_REPEATS = 1
N_TRIALS = 250

ERRORS_CSV_PATH = "data/trial_errors.csv"
MUTATION_MASKS_CSV_PATH = "data/mutation_masks.csv"

best_errors = []
global_seed = 0


def get_next_seed():
    global global_seed
    seed = global_seed
    global_seed += 1
    return seed


def simulate(**params) -> Tuple[bool, int]:
    model = RCCModel(comm=MPI.COMM_SELF, **params)

    while model.running:
        model.step()

    return model.survival, model.steps


def evaluate_case(row, params, n_repeats=N_REPEATS):
    case_errors = []
    for i in range(n_repeats):
        try:
            survival, steps = simulate(**params, random_seed=i, **row.to_dict())
            if survival == row["death"]:
                error = HIGH_PENALTY ** 2
            else:
                error = (steps - row["OS"]) ** 2
        except Exception as e:
            print(f"Simulation error (seed={i}): {e}")
            error = HIGH_PENALTY ** 2
        case_errors.append(error)
    return np.mean(case_errors)


def objective(trial: optuna.Trial, df) -> float:
    params = suggest_parameters(trial)
    errors = []
    for i, row in df.iterrows():
        case_error = evaluate_case(row, params)
        errors.append(case_error)

    trial_error = float(np.mean(errors))

    if best_errors:
        best_so_far = min(best_errors[-1], trial_error)
    else:
        best_so_far = trial_error
    best_errors.append(best_so_far)

    os.makedirs(os.path.dirname(ERRORS_CSV_PATH), exist_ok=True)
    file_exists = os.path.isfile(ERRORS_CSV_PATH)
    with open(ERRORS_CSV_PATH, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["trial_number", "trial_error", "best_error_so_far", "parameters"])
        writer.writerow([trial.number, trial_error, best_so_far, json.dumps(params)])

    return trial_error


def load_dataset(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file {file_path} does not exist.")

    def treatment_to_list(treatment_str):
        return [t.strip() for t in treatment_str.split('+')]

    return pd.read_csv(file_path, converters={"treatment": treatment_to_list})


if __name__ == "__main__":
    df = load_dataset("data/ARON.csv")
    print(df)

    def wrapped_objective(trial):
        return objective(trial, df)

    study = optuna.create_study(direction="minimize")
    study.optimize(wrapped_objective, n_trials=N_TRIALS)

    print("Best parameters:", study.best_params)
    print("Best value (error):", study.best_value)

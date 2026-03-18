# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Patient-specific parameters for the RCC simulation.

Includes biological sex, BMI, treatment selection, treatment start
time, and initial immune/tumor cell concentrations (cells/mL).
"""
from dataclasses import dataclass
from enum import Enum

from src.parameters.parameters import Parameters


class Sex(str, Enum):
    """Biological sex of the patient."""

    FEMALE = 'F'
    MALE = 'M'


class TreatmentType(str, Enum):
    """Available treatment drug combinations."""

    NONE = 'None'
    ICI = 'ICI'
    TKI = 'TKI'
    ICI_TKI = 'ICI+TKI'


@dataclass
class PatientParameters(Parameters):
    """Patient attributes and initial cell concentrations.

    Concentrations are in cells/mL and are scaled by model volume
    during initialization to determine actual agent counts.
    """

    sex: Sex = Sex.FEMALE
    BMI: float = 22.0
    treatment: TreatmentType = TreatmentType.ICI_TKI
    treatment_start: int = 100
    ctc_concentration: int = 80000
    neutrophil_concentration: int = 40000
    mast_cell_concentration: int = 40000
    treg_concentration: int = 40000
    pdc_concentration: int = 40000
    th1_concentration: int = 40000
    th2_concentration: int = 40000
    dc_concentration: int = 80000
    m1_concentration: int = 40000
    m2_concentration: int = 40000
    nkl_concentration: int = 160000
    cd4_concentration: int = 80000
    cd8_concentration: int = 80000

    param_labels = {
        "sex": "Sex (F/M)",
        "BMI": "Body Mass Index (kg/m²)",
        "treatment": "Drugs used in Treatment (ICI/TKI)",
        "treatment_start": "Treatment Start (steps)",
        "ctc_concentration": "CTC Concentration (cells/mL)",
        "neutrophil_concentration": "Neutrophil Concentration (cells/mL)",
        "mast_cell_concentration": "Mast Cell Concentration (cells/mL)",
        "treg_concentration": "Treg Cell Concentration (cells/mL)",
        "pdc_concentration": "PDC Concentration (cells/mL)",
        "th1_concentration": "Th1 Cell Concentration (cells/mL)",
        "th2_concentration": "Th2 Cell Concentration (cells/mL)",
        "dc_concentration": "DC Concentration (cells/mL)",
        "m1_concentration": "M1 Macrophage Concentration (cells/mL)",
        "m2_concentration": "M2 Macrophage Concentration (cells/mL)",
        "nkl_concentration": "NKL Cell Concentration (cells/mL)",
        "cd4_concentration": "CD4 T Cell Concentration (cells/mL)",
        "cd8_concentration": "CD8 T Cell Concentration (cells/mL)",
    }
    param_steps = {
        "BMI": 0.1,
        "treatment_start": 1,
        "ctc_concentration": 1000,
        "neutrophil_concentration": 1000,
        "mast_cell_concentration": 1000,
        "treg_concentration": 1000,
        "pdc_concentration": 1000,
        "th1_concentration": 1000,
        "th2_concentration": 1000,
        "dc_concentration": 1000,
        "m1_concentration": 1000,
        "m2_concentration": 1000,
        "nkl_concentration": 1000,
        "cd4_concentration": 1000,
        "cd8_concentration": 1000,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Agent type registry for Repast4Py.

Each agent type gets an integer ID required by repast4py.core.Agent(id, type, rank).
"""
from enum import IntEnum


class AgentType(IntEnum):
    """Integer enum of all agent types in the RCC model.

    Each value is the ``type`` argument passed to ``repast4py.core.Agent``.
    """

    TUMOR_CELL = 0
    CD8_CYTOTOXIC_T_CELL = 1
    CD8_NAIVE_T_CELL = 2
    CD4_NAIVE_T_CELL = 3
    CD4_HELPER1_T_CELL = 4
    CD4_HELPER2_T_CELL = 5
    REGULATORY_T_CELL = 6
    DENDRITIC_CELL = 7
    PLASMACITOID_DC = 8
    MACROPHAGE_M1 = 9
    MACROPHAGE_M2 = 10
    NATURAL_KILLER = 11
    MAST_CELL = 12
    NEUTROPHIL = 13
    ADIPOCYTE = 14
    BLOOD = 15
    SEX_HORMONE = 16
    CYTOKINE = 17

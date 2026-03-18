# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Simulation-level configuration parameters.

Defines volume, spatial resolution, random seed, and step limit
for the RCC agent-based model.
"""
from dataclasses import dataclass
from src.parameters.parameters import Parameters


@dataclass
class ModelParameters(Parameters):
    """Core simulation parameters (grid size, seed, max steps)."""

    volume: float = 0.0001
    block_size: int = 10
    random_seed: int = 1
    max_steps: int = 500

    param_labels = {
        "volume": "Volume (mL)",
        "block_size": "Block Size (μm)",
        "random_seed": "Random Seed"
    }
    param_steps = {
        "volume": 0.000001,
        "block_size": 1,
        "random_seed": 1
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Cytokine base class (abstract, placeholder for future extension)."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType


class Cytokine(Cell):
    """Abstract cytokine agent placeholder for future signaling extensions."""

    def __init__(self, local_id, rank, model, pos):
        """Initialize a cytokine agent."""
        super().__init__(local_id, AgentType.CYTOKINE, rank, model, pos)

    def step(self):
        """No-op step; reserved for future cytokine diffusion logic."""
        pass

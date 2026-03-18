# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Dendritic Cell — phagocytoses tumors, activates T cells, glucose chemotaxis fallback."""
from src.agents.cell import Cell
from src.agents.phagocytic_mixin import PhagocyticMixin
from src.agents.agent_types import AgentType


class DendriticCell(PhagocyticMixin, Cell):
    """Conventional dendritic cell specializing in antigen presentation.

    Hunts tumor cells via chemotaxis, phagocytoses them, then migrates
    towards naive T cells to present captured antigens and trigger
    adaptive immune activation.
    """

    def __init__(self, local_id, rank, model, pos):
        """Initialize a dendritic cell with extended search range and phagocytosis state."""
        super().__init__(local_id, AgentType.DENDRITIC_CELL, rank, model, pos)
        self.experienced_effects.dc_phagocytosis_effect += self.initial_phagocytosis_chance
        self.search_dimension += 10
        self._init_phagocytosis()

    def step(self):
        """Hunt and phagocytose tumors, or present captured antigen to T cells."""
        if self.base_step():
            return

        if not self._has_phagocytosed:
            self.move_towards_or_chemotaxis(AgentType.TUMOR_CELL, self.search_dimension)
            self.attempt_phagocytosis(self._phagocytosis_probability())
            self.consume_glucose()
        else:
            if self.present_to_t_cell():
                self.reset_phagocytosis()

    needs_effect = True

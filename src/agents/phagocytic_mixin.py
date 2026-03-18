# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Mixin for phagocytic cells (Template Method pattern).

Provides common phagocytosis state machine:
  hunt phase → engulf tumor → present to T cell → reset

Subclasses override hook methods to customize behavior.
"""
from src.agents.agent_types import AgentType


class PhagocyticMixin:
    """Mixin providing phagocytosis state and operations.

    Requires the host class to be a Cell subclass with:
        - self.model, self.pos, self.search_dimension
        - self.find_one(), self.move_towards(), self.record_kill()
    """

    max_presentation_attempts = 10

    def _init_phagocytosis(self, t_cell_types=None):
        """Initialize phagocytosis state. Call from subclass __init__."""
        self._has_phagocytosed = False
        self._phagocytosed_cell = None
        self._presentation_attempts = 0
        if t_cell_types is None:
            t_cell_types = [AgentType.CD4_NAIVE_T_CELL, AgentType.CD8_NAIVE_T_CELL]
        self._presentation_target = self.model.rng.choice(t_cell_types)

    # Default phagocytosis chance — override initial_phagocytosis_chance in subclass
    initial_phagocytosis_chance = 0.5

    def _phagocytosis_probability(self):
        """Compute phagocytosis probability from DC-style effects and weights."""
        wp = self.model.weight_params
        return (self.experienced_effects.dc_phagocytosis_effect * wp.w_dc_phagocytosis_effect +
                wp.b_dc_phagocytosis)

    def attempt_phagocytosis(self, probability, target_type=AgentType.TUMOR_CELL):
        """Try to engulf a nearby target cell.

        Args:
            probability: Probability of successful phagocytosis.
            target_type: AgentType to target.

        Returns:
            True if phagocytosis succeeded, False otherwise.
        """
        nearby = self.find_one(target_type)
        if nearby is not None and self.model.rng.random() < probability:
            self._phagocytosed_cell = nearby
            self.model.remove_agent(nearby)
            self._has_phagocytosed = True
            self.record_kill()
            return True
        return False

    def present_to_t_cell(self, radius=1):
        """Move towards and attempt to present antigen to a T cell.

        Automatically resets phagocytosis state after max_presentation_attempts
        failed attempts, preventing the cell from being stuck indefinitely.

        Args:
            radius: Search radius for finding nearby T cells.

        Returns:
            True if antigen was presented, False otherwise.
        """
        self.move_towards(self._presentation_target, look_up_size=self.search_dimension)
        nearby_tcell = self.find_one(self._presentation_target, radius=radius)
        if nearby_tcell:
            nearby_tcell.activate(self._phagocytosed_cell)
            self._presentation_attempts = 0
            return True
        self._presentation_attempts += 1
        if self._presentation_attempts >= self.max_presentation_attempts:
            self.reset_phagocytosis()
        return False

    def can_receive_neoantigen(self):
        """Whether this cell can accept a neoantigen for presentation."""
        return not self._has_phagocytosed

    def receive_neoantigen(self, cell):
        """Receive a neoantigen-bearing cell for presentation (e.g. from TKI-induced apoptosis).

        Properly sets both phagocytosis state flags.
        """
        self._phagocytosed_cell = cell
        self._has_phagocytosed = True

    def reset_phagocytosis(self):
        """Reset phagocytosis state."""
        self._has_phagocytosed = False
        self._phagocytosed_cell = None
        self._presentation_attempts = 0

# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Immune Checkpoint Inhibitor (ICI) drug.

Blocks PD-1/PD-L1, restores T cell activity, increases immune infiltration.
"""
from src.agents.agent_types import AgentType
from src.treatments.drug import Drug


class ICIDrug(Drug):
    """Immune Checkpoint Inhibitor drug.

    Blocks the PD-1/PD-L1 pathway on tumor cells, restores T cell
    activation, and boosts immune infiltration of helper T cells
    and mast cells.
    """

    def step(self, proportion=1.0):
        """Apply ICI effects for one simulation step.

        Args:
            proportion: Fraction of full effectiveness (set by Treatment).
        """
        effectiveness = proportion * self.model.weight_params.w_ici_effectiveness

        # Set PD-1/PD-L1 inhibition for X% of tumor cells
        self.apply_to_type(AgentType.TUMOR_CELL, effectiveness,
                           lambda tc: setattr(tc, 'ICI_effect', True))

        # Restore T cell activity
        t_cell_types = [
            AgentType.CD8_CYTOTOXIC_T_CELL, AgentType.CD8_NAIVE_T_CELL,
            AgentType.CD4_NAIVE_T_CELL, AgentType.CD4_HELPER1_T_CELL,
            AgentType.CD4_HELPER2_T_CELL, AgentType.REGULATORY_T_CELL
        ]
        for type_id in t_cell_types:
            self.apply_to_type(type_id, effectiveness,
                               lambda t: setattr(t.experienced_effects, 't_activation_effect', 1.0))

        # Increase immune infiltration
        infiltrating_types = [AgentType.CD4_HELPER1_T_CELL, AgentType.CD4_HELPER2_T_CELL, AgentType.MAST_CELL]
        for type_id in infiltrating_types:
            self.apply_to_type(type_id, effectiveness,
                               lambda a: setattr(a, 'immune_infiltration_factor', a.immune_infiltration_factor + 1))

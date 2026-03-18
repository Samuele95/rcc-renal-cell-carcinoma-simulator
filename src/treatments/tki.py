# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Tyrosine Kinase Inhibitor (TKI) drug.

Inhibits tumor proliferation, angiogenesis, releases neoantigens, reduces Tregs.
"""
from src.agents.agent_types import AgentType
from src.treatments.drug import Drug


class TKIDrug(Drug):
    """Tyrosine Kinase Inhibitor drug.

    Reduces tumor proliferation and angiogenesis, triggers neoantigen
    release (TKI_effect flag), and suppresses Treg differentiation.
    """

    def step(self, proportion=1.0):
        """Apply TKI effects for one simulation step.

        Args:
            proportion: Fraction of full effectiveness (set by Treatment).
        """
        effectiveness = proportion * self.model.weight_params.w_tki_effectiveness
        reduction = 1 - effectiveness

        for tumor_cell in self.model.iter_agents_by_type_id(AgentType.TUMOR_CELL):
            if self.model.rng.random() < effectiveness:
                tumor_cell.experienced_effects.tumour_growth_effect *= reduction
            if self.model.rng.random() < effectiveness:
                tumor_cell.experienced_effects.angiogenesis_effect *= reduction
            if self.model.rng.random() < effectiveness:
                tumor_cell.TKI_effect = True

        # Reduce Treg differentiation
        self.apply_to_type(AgentType.CD4_NAIVE_T_CELL, effectiveness,
                           lambda cd4: setattr(cd4.experienced_effects, 'treg_differentiation_effect',
                                               cd4.experienced_effects.treg_differentiation_effect * reduction))

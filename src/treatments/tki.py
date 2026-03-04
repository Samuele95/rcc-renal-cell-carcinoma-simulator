"""Tyrosine Kinase Inhibitor (TKI) drug.

Inhibits tumor proliferation, angiogenesis, releases neoantigens, reduces Tregs.
"""
from src.agents.agent_types import AgentType
from src.treatments.drug import Drug


class TKIDrug(Drug):

    def __init__(self, model):
        super().__init__(model)

    def step(self, proportion=1.0):
        effectiveness = proportion * self.model.weight_params.w_tki_effectiveness

        for tumor_cell in self.model.get_agents_by_type_id(AgentType.TUMOR_CELL):
            if self.model.rng.random() < effectiveness:
                tumor_cell.experienced_effects.tumour_growth_effect *= (1 - effectiveness)
            if self.model.rng.random() < effectiveness:
                tumor_cell.experienced_effects.angiogenesis_effect *= (1 - effectiveness)
            if self.model.rng.random() < effectiveness:
                tumor_cell.TKI_effect = True

        # Reduce Treg differentiation
        for cd4 in self.model.get_agents_by_type_id(AgentType.CD4_NAIVE_T_CELL):
            if self.model.rng.random() < effectiveness:
                cd4.experienced_effects.treg_differentiation_effect *= (1 - effectiveness)

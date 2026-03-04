"""Immune Checkpoint Inhibitor (ICI) drug.

Blocks PD-1/PD-L1, restores T cell activity, increases immune infiltration.
"""
from src.agents.agent_types import AgentType
from src.treatments.drug import Drug


class ICIDrug(Drug):

    def __init__(self, model):
        super().__init__(model)

    def step(self, proportion=1.0):
        effectiveness = proportion * self.model.weight_params.w_ici_effectiveness

        # Set PD-1/PD-L1 inhibition to False for X% of tumor cells
        for tumor_cell in self.model.get_agents_by_type_id(AgentType.TUMOR_CELL):
            if self.model.rng.random() < effectiveness:
                tumor_cell.ICI_effect = True

        # Restore T cell activity
        t_cell_types = [
            AgentType.CD8_CYTOTOXIC_T_CELL, AgentType.CD8_NAIVE_T_CELL,
            AgentType.CD4_NAIVE_T_CELL, AgentType.CD4_HELPER1_T_CELL,
            AgentType.CD4_HELPER2_T_CELL, AgentType.REGULATORY_T_CELL
        ]
        for type_id in t_cell_types:
            for t_cell in self.model.get_agents_by_type_id(type_id):
                if self.model.rng.random() < effectiveness:
                    t_cell.experienced_effects.t_activation_effect = 1.0

        # Increase immune infiltration
        infiltrating_types = [AgentType.CD4_HELPER1_T_CELL, AgentType.CD4_HELPER2_T_CELL, AgentType.MAST_CELL]
        for type_id in infiltrating_types:
            for immune_cell in self.model.get_agents_by_type_id(type_id):
                if self.model.rng.random() < effectiveness:
                    immune_cell.immune_infiltration_factor += 1

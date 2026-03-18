# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""CD4+ Naive T Cell — differentiates into Treg, activates TH1/TH2."""
from src.agents.t_cell import TCell
from src.agents.agent_types import AgentType


class CD4NaiveTCell(TCell):
    """Naive CD4+ T cell that differentiates into Treg, Th1, or Th2.

    Without antigen activation, may spontaneously differentiate into a
    regulatory T cell (Treg) under hormonal influence. Upon antigen
    recognition, transforms into either a Th1 or Th2 helper cell based
    on the w_cd4_th1_ratio weight parameter.

    Attributes:
        receptor: Randomly generated 8-bit TCR receptor for antigen matching.
    """

    initial_treg_differentiation = 0.005

    def __init__(self, local_id, rank, model, pos):
        """Initialize a naive CD4+ T cell with a random receptor."""
        super().__init__(local_id, AgentType.CD4_NAIVE_T_CELL, rank, model, pos)
        self.receptor = self.generate_receptor()
        self.experienced_effects.treg_differentiation_effect += self.initial_treg_differentiation

    def step(self):
        """Perceive hormones and attempt Treg differentiation each tick."""
        if self.base_step():
            return

        E, P, T = self.perceive_all_hormones(e_qty=3, p_qty=2, t_qty=2)

        x = -6.0 + 1.2 * E + 1.0 * P + 0.4 * T
        p_treg_gene = self.sigmoid(x)

        p_final = (
            (self.experienced_effects.treg_differentiation_effect * self.model.weight_params.w_cd4_treg_diff_effect +
             p_treg_gene * self.model.weight_params.w_cd4_treg_diff_horm) / 2 +
            self.model.weight_params.b_cd4_treg_diff
        )
        if self.model.rng.random() < p_final:
            from src.agents.regulatory_t_cell import TregCell
            self.transform_into(TregCell)
            return

    def activate(self, tumour_cell):
        """Activate into Th1 or Th2 helper cell if antigen matches receptor."""
        antigen = tumour_cell.get_antigen()
        if self.pos is not None and antigen is not None and self.is_matching(antigen, self.receptor):
            if self.model.rng.random() < self.model.weight_params.w_cd4_th1_ratio:
                from src.agents.cd4_t_cell_h1 import CD4Helper1TCell
                self.transform_into(CD4Helper1TCell)
            else:
                from src.agents.cd4_t_cell_h2 import CD4Helper2TCell
                self.transform_into(CD4Helper2TCell)
            return True
        return False

    needs_effect = True



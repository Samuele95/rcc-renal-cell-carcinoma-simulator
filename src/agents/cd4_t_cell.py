"""CD4+ Naive T Cell — differentiates into Treg, activates TH1/TH2."""
from src.agents.t_cell import TCell
from src.agents.sex_hormone import SexHormoneType
from src.agents.agent_types import AgentType


class CD4NaiveTCell(TCell):
    initial_treg_differentiation = 0.005

    def __init__(self, local_id, rank, model, pos):
        super().__init__(local_id, AgentType.CD4_NAIVE_T_CELL, rank, model, pos)
        self.receptor = self.generate_receptor()
        self.experienced_effects.treg_differentiation_effect += self.initial_treg_differentiation

    def step(self):
        self.apply_hormonal_decay()
        if self.pos is None:
            return

        self.perceive_sex_hormone(SexHormoneType.ESTROGEN, quantity=3, search_radius=2)
        self.perceive_sex_hormone(SexHormoneType.PROGESTERONE, quantity=2, search_radius=2)
        self.perceive_sex_hormone(SexHormoneType.TESTOSTERONE, quantity=2, search_radius=2)

        E = self.sex_hormone_stimulation_level(SexHormoneType.ESTROGEN)
        P = self.sex_hormone_stimulation_level(SexHormoneType.PROGESTERONE)
        T = self.sex_hormone_stimulation_level(SexHormoneType.TESTOSTERONE)

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
        antigen = tumour_cell.get_antigen()
        if self.pos is not None and antigen is not None and self.is_matching(antigen, self.receptor):
            if self.model.rng.random() < 0.5:
                from src.agents.cd4_t_cell_h1 import CD4Helper1TCell
                self.transform_into(CD4Helper1TCell)
            else:
                from src.agents.cd4_t_cell_h2 import CD4Helper2TCell
                self.transform_into(CD4Helper2TCell)
            return True
        return False

    needs_effect = True



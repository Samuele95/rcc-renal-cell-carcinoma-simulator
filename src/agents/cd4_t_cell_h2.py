"""CD4+ Helper 2 T Cell — produces IL-4/IL-5/IL-13, recruits CT and M1."""
from src.agents.t_cell import TCell
from src.agents.sex_hormone import SexHormoneType
from src.agents.agent_types import AgentType
from src.systems.effect import Effect


class CD4Helper2TCell(TCell):
    spawn_m1_chance = 0.01
    spawn_t_chance = 0.01
    initial_proliferation_chance = 0.01
    my_t_kill_rate_effect = 0.01
    my_tumour_growth_effect = 0.01

    def __init__(self, local_id, rank, model, pos):
        super().__init__(local_id, AgentType.CD4_HELPER2_T_CELL, rank, model, pos)
        self.experienced_effects.th2_proliferation_effect += self.initial_proliferation_chance
        self.experienced_effects.t_activation_effect = self.initial_t_activation_effect
        self._cached_effect = Effect()
        self._cached_effect.t_kill_rate_effect = self.my_t_kill_rate_effect
        self._cached_effect.tumour_growth_effect = self.my_tumour_growth_effect

    def step(self):
        if super().base_step():
            return

        wp = self.model.weight_params
        self.apply_hormonal_decay()

        self.perceive_sex_hormone(SexHormoneType.ESTROGEN, 2, 2)
        self.perceive_sex_hormone(SexHormoneType.PROGESTERONE, 1, 2)

        E = self.sex_hormone_stimulation_level(SexHormoneType.ESTROGEN)
        P = self.sex_hormone_stimulation_level(SexHormoneType.PROGESTERONE)

        x = -6.0 + 1.5 * E + 0.3 * P
        gene_factor = self.sigmoid(x)

        p_proliferation = (
            (self.experienced_effects.th2_proliferation_effect * wp.w_cd4_th2_proliferation_effect +
             gene_factor * wp.w_cd4_th2_proliferation_horm +
             wp.b_cd4_th2_proliferation) * self.experienced_effects.t_activation_effect
        )
        p_spawn_m1 = self.spawn_m1_chance * wp.w_cd4_th2_spawn_m1 * self.experienced_effects.t_activation_effect
        p_spawn_t = self.spawn_t_chance * wp.w_cd4_th2_spawn_t * self.experienced_effects.t_activation_effect

        if self.model.rng.random() < p_spawn_m1:
            from src.agents.macrophage_m1 import MacrophageM1
            self.spawn_at_entry(MacrophageM1)

        if self.model.rng.random() < p_spawn_t:
            from src.agents.cd8_cytotoxic_t_cell import CytotoxicTCell
            self.spawn_at_entry(CytotoxicTCell)

        if self.model.rng.random() < p_proliferation:
            self.duplicate()

        self.move_towards(AgentType.TUMOR_CELL, self.search_dimension)
        self.immune_infiltration_factor = 1

    def get_effect(self):
        return self._cached_effect

    has_effect = True

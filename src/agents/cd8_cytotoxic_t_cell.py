"""Cytotoxic T Cell (activated CD8+) with glucose chemotaxis fallback."""
from src.agents.t_cell import TCell
from src.agents.sex_hormone import SexHormoneType
from src.agents.agent_types import AgentType


class CytotoxicTCell(TCell):
    initial_kill_chance = 0.25
    proliferation_chance = 0.015
    pd1_inhibition = 0.5

    def __init__(self, local_id, rank, model, pos):
        super().__init__(local_id, AgentType.CD8_CYTOTOXIC_T_CELL, rank, model, pos)
        self.experienced_effects.t_kill_rate_effect += self.initial_kill_chance
        self.experienced_effects.t_activation_effect = self.initial_t_activation_effect

    def step(self):
        if super().base_step():
            return

        self.apply_sex_hormones_stimulation()

        wp = self.model.weight_params
        eff = self.experienced_effects

        p_apoptosis = eff.t_apoptosis_effect * wp.w_cytotoxic_apoptosis + wp.b_cytotoxic_apoptosis
        p_proliferation = self.proliferation_chance * wp.w_cytotoxic_proliferation * eff.t_activation_effect
        p_kill = (eff.t_kill_rate_effect * wp.w_cytotoxic_kill + wp.b_cytotoxic_kill) * eff.t_activation_effect

        # Glucose impairment
        p_kill *= self.glucose_impairment_factor()
        self.consume_glucose()

        if self.model.rng.random() < p_apoptosis:
            self.model.remove_agent(self)
            return

        if self.model.rng.random() < p_proliferation:
            self.duplicate()

        # Movement + Attack
        move_radius = int(self.search_dimension * wp.w_cytotoxic_move)
        self.move_towards_or_chemotaxis(AgentType.TUMOR_CELL, look_up_size=move_radius)

        nearby_tumor = self.find_one(AgentType.TUMOR_CELL)
        if nearby_tumor and self.model.rng.random() < p_kill:
            if not nearby_tumor.get_PD1_inhibition():
                self.model.remove_agent(nearby_tumor)
                self.record_kill()
                self.experienced_effects.t_activation_effect -= wp.w_progressive_exhaustion
            else:
                self.experienced_effects.t_activation_effect = max(
                    0, self.experienced_effects.t_activation_effect - self.pd1_inhibition * wp.w_gene_pd1_inhibition
                )

    needs_effect = True

    def apply_sex_hormones_stimulation(self):
        self.apply_hormonal_decay()

        self.perceive_sex_hormone(SexHormoneType.ESTROGEN, quantity=1, search_radius=2)
        self.perceive_sex_hormone(SexHormoneType.PROGESTERONE, quantity=1, search_radius=2)
        self.perceive_sex_hormone(SexHormoneType.TESTOSTERONE, quantity=1, search_radius=2)

        E = self.sex_hormone_stimulation_level(SexHormoneType.ESTROGEN)
        P = self.sex_hormone_stimulation_level(SexHormoneType.PROGESTERONE)
        T = self.sex_hormone_stimulation_level(SexHormoneType.TESTOSTERONE)

        wp = self.model.weight_params
        self.experienced_effects.t_kill_rate_effect += 0.1 * wp.w_sex_hormone_cd8 * E
        self.proliferation_chance += 0.005 * wp.w_sex_hormone_cd8 * E
        self.experienced_effects.t_apoptosis_effect -= 0.005 * wp.w_sex_hormone_cd8 * E
        self.experienced_effects.t_kill_rate_effect -= 0.1 * wp.w_sex_hormone_cd8 * T
        self.proliferation_chance -= 0.005 * wp.w_sex_hormone_cd8 * T
        self.experienced_effects.t_apoptosis_effect += 0.005 * wp.w_sex_hormone_cd8 * T
        self.proliferation_chance -= 0.005 * wp.w_sex_hormone_cd8 * P
        self.experienced_effects.t_apoptosis_effect += 0.005 * wp.w_sex_hormone_cd8 * P

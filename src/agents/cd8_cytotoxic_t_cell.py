# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Cytotoxic T Cell (activated CD8+) with glucose chemotaxis fallback."""
from src.agents.t_cell import TCell
from src.agents.agent_types import AgentType


class CytotoxicTCell(TCell):
    """Activated CD8+ cytotoxic T cell, the primary adaptive tumor killer.

    Seeks tumor cells via chemotaxis, kills on contact subject to PD-1
    checkpoint inhibition, and undergoes progressive exhaustion after kills.
    Hormone levels modulate kill rate, proliferation, and apoptosis.

    Attributes:
        initial_kill_chance: Base kill probability before effect modulation.
        proliferation_chance: Base self-replication probability per tick.
        pd1_inhibition: Activation penalty when PD-1 inhibited by tumor.
    """

    initial_kill_chance = 0.25
    proliferation_chance = 0.015
    pd1_inhibition = 0.5

    def __init__(self, local_id, rank, model, pos):
        """Initialize a cytotoxic T cell with baseline kill and activation effects."""
        super().__init__(local_id, AgentType.CD8_CYTOTOXIC_T_CELL, rank, model, pos)
        self.experienced_effects.t_kill_rate_effect += self.initial_kill_chance
        self.experienced_effects.t_activation_effect = self.initial_t_activation_effect

    def step(self):
        """Hunt tumors, attempt kills with glucose/hormone modulation, and proliferate."""
        if self.base_step():
            return

        hormone_mod = self._compute_hormone_modifiers()

        wp = self.model.weight_params
        eff = self.experienced_effects

        p_apoptosis = (eff.t_apoptosis_effect + hormone_mod.apoptosis) * wp.w_cytotoxic_apoptosis + wp.b_cytotoxic_apoptosis
        p_proliferation = (self.proliferation_chance + hormone_mod.proliferation) * wp.w_cytotoxic_proliferation * eff.t_activation_effect
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

    class _HormoneModifiers:
        __slots__ = ('proliferation', 'apoptosis')
        def __init__(self, proliferation, apoptosis):
            self.proliferation = proliferation
            self.apoptosis = apoptosis

    def _compute_hormone_modifiers(self):
        """Perceive hormones and return per-step modifiers (non-mutating)."""
        E, P, T = self.perceive_all_hormones(e_qty=1, p_qty=1, t_qty=1)

        wp = self.model.weight_params
        w = wp.w_sex_hormone_cd8
        # Apply kill rate modifier directly (additive on accumulated effects is intentional)
        self.experienced_effects.t_kill_rate_effect += 0.1 * w * (E - T)
        return self._HormoneModifiers(
            proliferation=0.005 * w * (E - T - P),
            apoptosis=0.005 * w * (-E + T + P),
        )

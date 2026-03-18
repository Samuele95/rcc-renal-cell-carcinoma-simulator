# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Plasmacitoid Dendritic Cell — phagocytoses, activates T cells, spawns NK."""
from src.agents.cell import Cell
from src.agents.phagocytic_mixin import PhagocyticMixin
from src.agents.agent_types import AgentType
from src.systems.effect import Effect


class PlasmacitoidDendriticCell(PhagocyticMixin, Cell):
    """Plasmacytoid dendritic cell with dual immune modulation.

    Phagocytoses tumors and presents antigens like conventional DCs, but
    also spawns NK cells upon successful presentation. Emits mixed effects:
    boosts T cell and NK kill rates while promoting Treg differentiation
    and angiogenesis.
    """

    my_angiogenesis_effect = 0.01
    my_treg_differentiation_effect = 0.02
    my_t_proliferation_effect = -0.01
    my_t_kill_rate_effect = 0.25
    my_nkl_kill_rate_effect = 0.25
    spawn_nkl_chance = 0.01
    activation_range = 1

    def __init__(self, local_id, rank, model, pos):
        """Initialize a pDC with phagocytosis state and mixed immune effects."""
        super().__init__(local_id, AgentType.PLASMACITOID_DC, rank, model, pos)
        self.experienced_effects.dc_phagocytosis_effect += self.initial_phagocytosis_chance
        self.search_dimension += 10
        self._init_phagocytosis()
        wp = model.weight_params
        self._cached_effect = Effect.create(
            angiogenesis_effect=self.my_angiogenesis_effect * wp.w_pdc_angiogenesis,
            treg_differentiation_effect=self.my_treg_differentiation_effect * wp.w_pdc_treg_diff,
            t_proliferation_effect=self.my_t_proliferation_effect * wp.w_pdc_t_proliferation,
            t_kill_rate_effect=self.my_t_kill_rate_effect * wp.w_pdc_t_kill,
            nkl_kill_rate_effect=self.my_nkl_kill_rate_effect * wp.w_pdc_nkl_kill,
        )

    def step(self):
        """Hunt tumors, phagocytose, present antigen to T cells, and spawn NK cells."""
        if self.base_step():
            return

        if not self._has_phagocytosed:
            self.move_towards(AgentType.TUMOR_CELL, look_up_size=self.search_dimension)
            self.attempt_phagocytosis(self._phagocytosis_probability())
            self.consume_glucose()
            return

        if self.present_to_t_cell(radius=self.activation_range):
            self._try_spawn_nkl()
            self.reset_phagocytosis()

    def _try_spawn_nkl(self):
        """Attempt to spawn an NK cell in an adjacent empty position."""
        wp = self.model.weight_params
        p_spawn = self.spawn_nkl_chance * wp.w_pdc_nkl_spawn + wp.b_pdc_nkl_spawn
        if self.model.rng.random() < p_spawn:
            empty = self.get_empty_ngbhs()
            if empty:
                from src.agents.natural_killer import NaturalKiller
                nk = NaturalKiller(self.model.next_id(), self.model.rank, self.model, empty[0])
                self.model.add_agent(nk)

    has_effect = True

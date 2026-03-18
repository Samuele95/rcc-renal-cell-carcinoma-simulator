# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""M2 Macrophage — anti-inflammatory, pro-tumorigenic."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType
from src.systems.effect import Effect


class MacrophageM2(Cell):
    """M2 (alternatively activated) macrophage with pro-tumorigenic activity.

    Promotes tumor growth and angiogenesis while suppressing T cell kill
    rates. Can re-polarize back into anti-tumor M1 under appropriate
    microenvironment signals.
    """

    initial_mutation_chance = 0.1
    my_angiogenesis_effect = 0.01
    my_tumor_growth_effect = 0.01
    my_t_kill_rate_effect = -0.1

    def __init__(self, local_id, rank, model, pos):
        """Initialize an M2 macrophage with pro-tumorigenic effect cache."""
        super().__init__(local_id, AgentType.MACROPHAGE_M2, rank, model, pos)
        self.experienced_effects.macrophage_m2_mutation_effect += self.initial_mutation_chance
        wp = model.weight_params
        self._cached_effect = Effect.create(
            t_kill_rate_effect=self.my_t_kill_rate_effect * wp.w_m2_t_kill_rate,
            tumour_growth_effect=self.my_tumor_growth_effect * wp.w_m2_tumour_growth,
            angiogenesis_effect=self.my_angiogenesis_effect * wp.w_m2_angiogenesis,
        )

    def step(self):
        """Check M1 re-polarization, consume glucose, and move towards tumor."""
        if self.base_step():
            return
        rng = self.model.rng
        wp = self.model.weight_params

        self.consume_glucose()

        mut_thr = self.experienced_effects.macrophage_m2_mutation_effect * wp.w_m2_mutation + wp.b_m2_mutation
        if rng.random() < mut_thr:
            self._transform_to_macrophage_m1()
            return
        self.move_towards(AgentType.TUMOR_CELL, look_up_size=int(self.search_dimension * wp.w_m2_move))

    def _transform_to_macrophage_m1(self):
        """Re-polarize into an M1 macrophage at the same position."""
        from src.agents.macrophage_m1 import MacrophageM1
        self.transform_into(MacrophageM1)

    has_effect = True
    needs_effect = True

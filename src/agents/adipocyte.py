# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Adipocyte — fat cell that secretes pro-tumorigenic cytokines."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType
from src.systems.effect import Effect


class Adipocyte(Cell):
    """Adipocyte (fat cell) that promotes tumor growth via paracrine signaling.

    Stationary cell representing perinephric fat. Emits pro-tumorigenic
    growth signals and promotes M1-to-M2 macrophage polarization, modeling
    the obesity-cancer link in RCC.
    """

    my_tumour_growth_effect = 0.005
    my_m2_mutation_effect = 0.01

    def __init__(self, local_id, rank, model, pos):
        """Initialize an adipocyte with tumour growth and M2 polarization effects."""
        super().__init__(local_id, AgentType.ADIPOCYTE, rank, model, pos)
        wp = model.weight_params
        self._cached_effect = Effect.create(
            tumour_growth_effect=self.my_tumour_growth_effect * wp.w_adipocyte_tumour_growth,
            macrophage_m2_mutation_effect=self.my_m2_mutation_effect * wp.w_adipocyte_m2_mutation,
        )

    def step(self):
        """Check for base death; adipocytes are otherwise stationary."""
        if self.base_step():
            return

    has_effect = True

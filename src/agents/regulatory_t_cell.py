# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Regulatory T Cell (Treg) — immunosuppressive."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType
from src.systems.effect import Effect


class TregCell(Cell):
    """Regulatory T cell (Treg) that suppresses anti-tumor immune responses.

    Emits negative effects on T cell kill rate, proliferation, activation,
    and dendritic cell phagocytosis, while promoting T cell apoptosis.
    Moves towards tumors to exert local immunosuppression.
    """

    my_t_kill_rate_effect = -0.3
    my_t_proliferation_effect = -0.03
    my_t_apoptosis_effect = 0.01
    my_t_activation_effect = -0.01
    my_dc_phagocytosis_effect = -0.1

    def __init__(self, local_id, rank, model, pos):
        """Initialize a Treg cell with immunosuppressive effect weights."""
        super().__init__(local_id, AgentType.REGULATORY_T_CELL, rank, model, pos)
        wp = model.weight_params
        self._cached_effect = Effect.create(
            t_kill_rate_effect=self.my_t_kill_rate_effect * wp.w_treg_t_kill_rate,
            t_proliferation_effect=self.my_t_proliferation_effect * wp.w_treg_t_proliferation,
            t_apoptosis_effect=self.my_t_apoptosis_effect * wp.w_treg_t_apoptosis,
            t_activation_effect=self.my_t_activation_effect * wp.w_treg_activation,
            dc_phagocytosis_effect=self.my_dc_phagocytosis_effect * wp.w_treg_dc_phagocytosis,
        )

    def step(self):
        """Move towards tumor cells to exert local immunosuppressive effects."""
        if self.base_step():
            return
        wp = self.model.weight_params
        move_radius = int(self.search_dimension * wp.w_treg_move)
        self.move_towards(AgentType.TUMOR_CELL, look_up_size=move_radius)

    has_effect = True

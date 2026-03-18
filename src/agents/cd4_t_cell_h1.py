# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""CD4+ Helper 1 T Cell — produces IFN-gamma, activates M1 macrophages and DCs."""
from src.agents.t_cell import TCell
from src.agents.agent_types import AgentType
from src.systems.effect import Effect


class CD4Helper1TCell(TCell):
    """CD4+ Th1 helper T cell promoting pro-inflammatory anti-tumor responses.

    Produces IFN-gamma-like signals that recruit M1 macrophages and dendritic
    cells, and emits a tumour apoptosis effect on neighboring tumor cells.
    Proliferation is modulated by sex hormones (suppressed by estrogen).
    """

    spawn_m1_chance = 0.01
    spawn_dc_chance = 0.01
    initial_proliferation_chance = 0.01
    my_tumour_apoptosis_effect = 1

    def __init__(self, local_id, rank, model, pos):
        """Initialize a Th1 helper cell with proliferation and apoptosis effects."""
        super().__init__(local_id, AgentType.CD4_HELPER1_T_CELL, rank, model, pos)
        self.experienced_effects.th1_proliferation_effect += self.initial_proliferation_chance
        self.experienced_effects.t_activation_effect = self.initial_t_activation_effect
        self._cached_effect = Effect.create(tumour_apoptosis_effect=self.my_tumour_apoptosis_effect)

    def step(self):
        """Proliferate, recruit M1 macrophages and DCs, and move towards tumor."""
        if self.base_step():
            return

        wp = self.model.weight_params
        E, P, T = self.perceive_all_hormones(e_qty=2, p_qty=1, t_qty=1)

        x = -8.0 + 2.0 * (1 - E) - 0.5 * P - 0.5 * T
        gene_factor = self.sigmoid(x)

        p_proliferation = (
            (self.experienced_effects.th1_proliferation_effect * wp.w_cd4_th1_proliferation_effect -
             gene_factor * wp.w_cd4_th1_proliferation_horm +
             wp.b_cd4_th1_proliferation) * self.experienced_effects.t_activation_effect
        )
        p_m1 = self.spawn_m1_chance * wp.w_cd4_th1_spawn_m1 * self.experienced_effects.t_activation_effect
        p_dc = self.spawn_dc_chance * wp.w_cd4_th1_spawn_dc * self.experienced_effects.t_activation_effect

        if self.model.rng.random() < p_m1:
            from src.agents.macrophage_m1 import MacrophageM1
            self.spawn_at_entry(MacrophageM1)

        if self.model.rng.random() < p_dc:
            from src.agents.dendritic_cell import DendriticCell
            self.spawn_at_entry(DendriticCell)

        if self.model.rng.random() < p_proliferation:
            self.duplicate()

        self.move_towards(AgentType.TUMOR_CELL, self.search_dimension)

    has_effect = True
    needs_effect = True

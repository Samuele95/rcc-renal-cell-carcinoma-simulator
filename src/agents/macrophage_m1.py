# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""M1 Macrophage — pro-inflammatory, phagocytoses tumors, glucose chemotaxis."""
from src.agents.cell import Cell
from src.agents.phagocytic_mixin import PhagocyticMixin
from src.agents.agent_types import AgentType
from src.systems.effect import Effect


class MacrophageM1(PhagocyticMixin, Cell):
    """M1 (classically activated) macrophage with anti-tumor activity.

    Phagocytoses tumor cells and presents antigens to naive T cells.
    Boosts T cell kill rate and Th1 proliferation via local effects.
    Can polarize into pro-tumorigenic M2 under microenvironment pressure.

    Attributes:
        melt_chance: Probability of digesting phagocytosed cell per tick.
        phagocytosis_chance: Base probability of engulfing a nearby tumor.
        initial_mutation_chance: Base probability of M1-to-M2 polarization.
    """

    melt_chance = 0.2
    phagocytosis_chance = 0.5
    initial_mutation_chance = 0.1
    my_t_kill_rate_effect = 0.1
    my_th1_proliferation_effect = 0.01

    def __init__(self, local_id, rank, model, pos):
        """Initialize an M1 macrophage with phagocytosis state and effect cache."""
        super().__init__(local_id, AgentType.MACROPHAGE_M1, rank, model, pos)
        self.experienced_effects.macrophage_m1_mutation_effect += self.initial_mutation_chance
        self._init_phagocytosis(t_cell_types=[AgentType.CD4_NAIVE_T_CELL])
        self._ticks_since_phago = 0
        wp = model.weight_params
        self._cached_effect = Effect.create(
            t_kill_rate_effect=self.my_t_kill_rate_effect * wp.w_m1_t_kill_rate,
            th1_proliferation_effect=self.my_th1_proliferation_effect * wp.w_m1_th1_proliferation,
        )

    def step(self):
        """Check M2 polarization, hunt/phagocytose tumors, digest or present antigen."""
        if self.base_step():
            return

        rng = self.model.rng
        wp = self.model.weight_params

        self.consume_glucose()

        # 1) Potential mutation into M2
        mut_thr = self.experienced_effects.macrophage_m1_mutation_effect * wp.w_m1_mutation + wp.b_m1_mutation
        if rng.random() < mut_thr:
            self._transform_to_macrophage_m2()
            return

        # 2) Hunt phase
        if not self._has_phagocytosed:
            moved = self.move_towards_or_chemotaxis(
                AgentType.TUMOR_CELL, look_up_size=int(self.search_dimension * wp.w_m1_move)
            )
            if not moved:
                phago_prob = self.phagocytosis_chance * wp.w_m1_phagocytosis
                self.attempt_phagocytosis(phago_prob)
                if self._has_phagocytosed:
                    self._ticks_since_phago = 0
            return

        # 3) Post-phagocytosis: digest or present
        self._ticks_since_phago += 1
        if rng.random() < self.melt_chance * wp.w_m1_digest:
            self.reset_phagocytosis()
            self._ticks_since_phago = 0
            return

        if self.present_to_t_cell():
            self.reset_phagocytosis()
            self._ticks_since_phago = 0

    def _transform_to_macrophage_m2(self):
        """Polarize into an M2 macrophage at the same position."""
        from src.agents.macrophage_m2 import MacrophageM2
        self.transform_into(MacrophageM2)

    has_effect = True
    needs_effect = True

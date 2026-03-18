# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Natural Killer Cell — innate cytotoxic, glucose chemotaxis fallback."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType
from src.systems.effect import Effect


class NaturalKiller(Cell):
    """Natural Killer (NK) cell of the innate immune system.

    Kills tumor cells without prior antigen priming. Uses glucose chemotaxis
    as a fallback movement strategy. Also boosts nearby T cell kill rates
    via a positive effect.

    Attributes:
        initial_kill_chance: Base NK kill probability.
        my_t_kill_rate_effect: Positive effect on neighboring T cell kill rate.
    """

    initial_kill_chance = 0.1
    my_t_kill_rate_effect = 0.1

    def __init__(self, local_id, rank, model, pos):
        """Initialize an NK cell with kill rate and T cell support effects."""
        super().__init__(local_id, AgentType.NATURAL_KILLER, rank, model, pos)
        self.experienced_effects.nkl_kill_rate_effect += self.initial_kill_chance
        wp = model.weight_params
        self._cached_effect = Effect.create(
            t_kill_rate_effect=self.my_t_kill_rate_effect * wp.w_nkl_t_kill_rate,
        )

    def step(self):
        """Consume glucose, move towards tumors via chemotaxis, and attempt kills."""
        if self.base_step():
            return
        wp = self.model.weight_params

        self.consume_glucose()

        self.move_towards_or_chemotaxis(AgentType.TUMOR_CELL, self.search_dimension)

        p_kill = (self.experienced_effects.nkl_kill_rate_effect * wp.w_natural_killer_kill_rate +
                  wp.b_natural_killer_kill_rate)
        p_kill *= self.glucose_impairment_factor()
        self.try_kill_nearby(AgentType.TUMOR_CELL, p_kill)

    has_effect = True
    needs_effect = True

"""Natural Killer Cell — innate cytotoxic, glucose chemotaxis fallback."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType
from src.systems.effect import Effect


class NaturalKiller(Cell):
    initial_kill_chance = 0.1
    my_t_kill_rate_effect = 0.1

    def __init__(self, local_id, rank, model, pos):
        super().__init__(local_id, AgentType.NATURAL_KILLER, rank, model, pos)
        self.experienced_effects.nkl_kill_rate_effect += self.initial_kill_chance
        wp = model.weight_params
        self._cached_effect = Effect.create(
            t_kill_rate_effect=self.my_t_kill_rate_effect * wp.w_nkl_t_kill_rate,
        )

    def step(self):
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

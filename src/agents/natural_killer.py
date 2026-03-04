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
        self._cached_effect = Effect()
        self._cached_effect.t_kill_rate_effect = self.my_t_kill_rate_effect * wp.w_nkl_t_kill_rate

    def step(self):
        if super().base_step():
            return
        wp = self.model.weight_params

        self.consume_glucose()

        self.move_towards_or_chemotaxis(AgentType.TUMOR_CELL, self.search_dimension)

        nearby = self.find_one(AgentType.TUMOR_CELL)
        if nearby is not None:
            p_kill = (self.experienced_effects.nkl_kill_rate_effect * wp.w_natural_killer_kill_rate +
                      wp.b_natural_killer_kill_rate)
            p_kill *= self.glucose_impairment_factor()
            if self.model.rng.random() < p_kill:
                self.model.remove_agent(nearby)
                self.record_kill()

    def get_effect(self):
        return self._cached_effect

    has_effect = True
    needs_effect = True

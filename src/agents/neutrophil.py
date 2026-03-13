"""Neutrophil — short-lived innate immune cell that kills tumor cells."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType


class Neutrophil(Cell):
    kill_chance = 0.3

    def __init__(self, local_id, rank, model, pos):
        super().__init__(local_id, AgentType.NEUTROPHIL, rank, model, pos)
        self.age = 0

    def step(self):
        if self.base_step():
            return
        self.age += 1
        if self.age > self.model.weight_params.neutrophil_max_lifespan:
            self.model.remove_agent(self)
            return
        self.move_towards_or_random_walk(AgentType.TUMOR_CELL, look_up_size=self.search_dimension)
        wp = self.model.weight_params
        p_kill = self.kill_chance * wp.w_neutrophil_kill_rate + wp.b_neutrophil_kill_rate
        self.try_kill_nearby(AgentType.TUMOR_CELL, p_kill)
        self.consume_glucose()

"""Neutrophil — short-lived innate immune cell that kills tumor cells."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType


class Neutrophil(Cell):
    kill_chance = 0.3
    max_lifespan = 15

    def __init__(self, local_id, rank, model, pos):
        super().__init__(local_id, AgentType.NEUTROPHIL, rank, model, pos)
        self.age = 0

    def step(self):
        if self.base_step():
            return
        self.age += 1
        if self.age > self.max_lifespan:
            self.model.remove_agent(self)
            return
        moved = self.move_towards(AgentType.TUMOR_CELL, look_up_size=self.search_dimension)
        if not moved:
            self.random_walk()
        p_kill = (
            self.kill_chance * self.model.weight_params.w_neutrophil_kill_rate +
            self.model.weight_params.b_neutrophil_kill_rate
        )
        nearby = self.find_one(AgentType.TUMOR_CELL)
        if nearby is not None and self.model.rng.random() < p_kill:
            self.model.remove_agent(nearby)
            self.record_kill()
        self.consume_glucose()

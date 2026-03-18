# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Neutrophil — short-lived innate immune cell that kills tumor cells."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType


class Neutrophil(Cell):
    """Short-lived innate immune cell that kills tumor cells on contact.

    Has a finite lifespan (neutrophil_max_lifespan ticks) after which it
    dies. Moves towards tumors with random walk fallback.

    Attributes:
        kill_chance: Base tumor kill probability per encounter.
        age: Number of ticks since creation.
    """

    kill_chance = 0.3

    def __init__(self, local_id, rank, model, pos):
        """Initialize a neutrophil with age counter at zero."""
        super().__init__(local_id, AgentType.NEUTROPHIL, rank, model, pos)
        self.age = 0

    def step(self):
        """Age, check lifespan, move towards tumors, attempt kills, consume glucose."""
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

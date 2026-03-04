"""Cytokine base class (abstract, placeholder for future extension)."""
from abc import ABC
from repast4py.core import Agent

from src.agents.agent_types import AgentType


class Cytokine(ABC, Agent):

    def __init__(self, local_id, rank, model, pos):
        super().__init__(id=local_id, type=AgentType.CYTOKINE, rank=rank)
        self.model = model
        self.pos = pos
        self._alive = True

    def step(self):
        pass

    def save(self):
        return (self.uid, (self.pos,))

"""Cytokine base class (abstract, placeholder for future extension)."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType


class Cytokine(Cell):

    def __init__(self, local_id, rank, model, pos):
        super().__init__(local_id, AgentType.CYTOKINE, rank, model, pos)

    def step(self):
        pass

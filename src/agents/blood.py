"""Blood vessel agent — glucose source in the microenvironment."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType


class Blood(Cell):
    has_step = False

    def __init__(self, local_id, rank, model, pos, tumour_generated=False):
        super().__init__(local_id, AgentType.BLOOD, rank, model, pos)
        self._tumour_generated = tumour_generated

    def is_tumour_generated(self):
        return self._tumour_generated

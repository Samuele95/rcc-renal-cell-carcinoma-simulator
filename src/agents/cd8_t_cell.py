"""CD8+ Naive T Cell that can activate into CytotoxicTCell."""
from src.agents.t_cell import TCell
from src.agents.agent_types import AgentType


class CD8NaiveTCell(TCell):

    def __init__(self, local_id, rank, model, pos):
        super().__init__(local_id, AgentType.CD8_NAIVE_T_CELL, rank, model, pos)
        self.receptor = self.generate_receptor()

    def step(self):
        if self.base_step():
            return
        self.random_walk()
        self.consume_glucose()

    def activate(self, tumor_cell):
        """Activate into CytotoxicTCell if antigen matches."""
        from src.agents.cd8_cytotoxic_t_cell import CytotoxicTCell
        antigen = tumor_cell.get_antigen()
        if self.pos is not None and antigen is not None and self.is_matching(antigen, self.receptor):
            self.transform_into(CytotoxicTCell)
            return True
        return False

    needs_effect = True

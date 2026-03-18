# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""CD8+ Naive T Cell that can activate into CytotoxicTCell."""
from src.agents.t_cell import TCell
from src.agents.agent_types import AgentType


class CD8NaiveTCell(TCell):
    """Naive CD8+ T cell that patrols randomly until antigen-activated.

    Upon recognizing a matching tumor neoantigen, differentiates into a
    CytotoxicTCell capable of direct tumor killing.

    Attributes:
        receptor: Randomly generated 8-bit TCR receptor for antigen matching.
    """

    def __init__(self, local_id, rank, model, pos):
        """Initialize a naive CD8+ T cell with a random receptor."""
        super().__init__(local_id, AgentType.CD8_NAIVE_T_CELL, rank, model, pos)
        self.receptor = self.generate_receptor()

    def step(self):
        """Random walk and consume glucose while awaiting activation."""
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

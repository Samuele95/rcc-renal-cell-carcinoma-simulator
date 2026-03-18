# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Blood vessel agent — glucose source in the microenvironment."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType


class Blood(Cell):
    """Blood vessel agent serving as a glucose source and immune entry point.

    Stationary agent (has_step=False) placed during model initialization
    or created by tumor angiogenesis. Glucose is diffused from blood vessel
    positions by the glucose field system.

    Attributes:
        has_step: Always False; blood vessels do not act during step().
    """

    has_step = False

    def __init__(self, local_id, rank, model, pos, tumour_generated=False):
        """Initialize a blood vessel.

        Args:
            local_id: Unique agent ID.
            rank: MPI rank.
            model: The RCCModel instance.
            pos: (x, y, z) grid position.
            tumour_generated: True if created by tumor angiogenesis.
        """
        super().__init__(local_id, AgentType.BLOOD, rank, model, pos)
        self._tumour_generated = tumour_generated

    def is_tumour_generated(self):
        """Return whether this vessel was created by tumor angiogenesis."""
        return self._tumour_generated

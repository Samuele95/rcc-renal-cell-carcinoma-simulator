# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Data collection observer for tracking tumor cell kills during simulation.

Maintains per-immune-cell-type kill counters and provides aggregate statistics
used by the model's data logging and the UI's results charts.
"""
from dataclasses import dataclass, field, asdict

from src.agents.agent_types import AgentType


# Maps agent type to the Observer field that tracks its kills
_KILL_FIELD_MAP = {
    AgentType.TUMOR_CELL: 'apoptosis_count',
    AgentType.MACROPHAGE_M1: 'm1_macrophage_kills',
    AgentType.DENDRITIC_CELL: 'dendritic_cell_kills',
    AgentType.PLASMACITOID_DC: 'pdc_kills',
    AgentType.CD8_CYTOTOXIC_T_CELL: 'cytotoxic_T_cell_kills',
    AgentType.NATURAL_KILLER: 'nkl_kill_count',
    AgentType.NEUTROPHIL: 'neutrophil_kills',
}


@dataclass
class Observer:
    """Tracks kill events by immune cell type throughout a simulation run.

    Each field counts the number of tumor cells killed by the corresponding
    immune cell type. Supports dict-like access via ``__getitem__``.
    """

    apoptosis_count: int = field(default=0)
    m1_macrophage_kills: int = field(default=0)
    dendritic_cell_kills: int = field(default=0)
    pdc_kills: int = field(default=0)
    cytotoxic_T_cell_kills: int = field(default=0)
    nkl_kill_count: int = field(default=0)
    neutrophil_kills: int = field(default=0)

    def record_kill(self, killer_type_id):
        """Increment the kill counter for the given agent type.

        Args:
            killer_type_id: AgentType IntEnum value of the killer.
        """
        field_name = _KILL_FIELD_MAP.get(killer_type_id)
        if field_name is not None:
            setattr(self, field_name, getattr(self, field_name) + 1)

    def total_kills(self):
        """Total immune kills (excludes apoptosis)."""
        return (self.m1_macrophage_kills + self.dendritic_cell_kills +
                self.pdc_kills + self.cytotoxic_T_cell_kills +
                self.nkl_kill_count + self.neutrophil_kills)

    def to_dict(self):
        """Return all kill counters as a plain dictionary."""
        return asdict(self)

    def __getitem__(self, item):
        """Allow dict-style access to kill counters by field name."""
        return getattr(self, item)

"""TCell base class for all T cell agents.

Ported from Mesa to Repast4Py. Provides hormone perception,
TCR receptor matching (Hamming distance, hash), and sex hormone modulation.
"""
import hashlib
from abc import ABC
from functools import lru_cache

from src.systems.dna import DNA
from src.systems import grid_utils
from src.agents.cell import Cell
from src.agents.agent_types import AgentType
from src.agents.sex_hormone import SexHormoneType


class TCell(Cell, ABC):
    """Base class for all T cell agents with hormone perception and TCR matching."""

    receptor: int
    initial_t_activation_effect: float = 1.0

    def __init__(self, local_id, agent_type, rank, model, pos):
        super().__init__(local_id, agent_type, rank, model, pos)
        self.perceived_sex_hormone = {
            SexHormoneType.TESTOSTERONE: 0,
            SexHormoneType.ESTROGEN: 0,
            SexHormoneType.PROGESTERONE: 0,
        }

    def activate(self, tumour_cell):
        """Attempt to activate the T cell with a tumour cell. Override in subclasses."""
        ...

    def hamming_distance(self, number1, number2):
        """Calculate Hamming distance between two integers."""
        number = number1 ^ number2
        distance = 0
        while number:
            distance += number & 0x1
            number >>= 1
        return distance

    @staticmethod
    @lru_cache(maxsize=1024)
    def amino_to_8bit_hash(seq):
        """Convert amino acid sequence to 8-bit hash (cached)."""
        digest = hashlib.sha256(seq.encode()).digest()
        return digest[0]

    def generate_receptor(self):
        """Generate a random 8-bit receptor value."""
        return self.model.rng.randint(0, 255)

    def is_matching(self, antigen, receptor):
        """Check if antigen matches receptor (recognized as foreign).

        An antigen is foreign if it's not a self-antigen and the Hamming distance
        to the receptor is within threshold.
        """
        return ((antigen not in DNA.self_antigens()) and
                self.hamming_distance(TCell.amino_to_8bit_hash(antigen), receptor) <=
                (3 + self.model.weight_params.receptor_threshold_variation))

    def sex_hormone_stimulation_level(self, hormone_type):
        """Return the perceived level of a sex hormone type."""
        return self.perceived_sex_hormone[hormone_type]

    def perceive_all_hormones(self, e_qty=1, p_qty=1, t_qty=0, radius=2):
        """Perceive all sex hormones and return stimulation levels.

        Single neighbor query instead of one per hormone type.

        Args:
            e_qty: Max estrogen hormones to perceive.
            p_qty: Max progesterone hormones to perceive.
            t_qty: Max testosterone hormones to perceive.
            radius: Search radius.

        Returns:
            (E, P, T) tuple of stimulation levels.
        """
        self.apply_hormonal_decay()

        if self.pos is None:
            return (
                self.sex_hormone_stimulation_level(SexHormoneType.ESTROGEN),
                self.sex_hormone_stimulation_level(SexHormoneType.PROGESTERONE),
                self.sex_hormone_stimulation_level(SexHormoneType.TESTOSTERONE),
            )

        # Single neighbor query for all hormone types
        neighbors = grid_utils.get_neighbors_3d(
            self.model.spatial_index, self.model.grid_dims,
            self.pos, radius=radius, moore=True
        )

        # Collect hormones by type with quantity limits
        cap = self.model.weight_params.w_hormone_perception_cap
        limits = {
            SexHormoneType.ESTROGEN: min(e_qty, cap),
            SexHormoneType.PROGESTERONE: min(p_qty, cap),
            SexHormoneType.TESTOSTERONE: min(t_qty, cap),
        }
        found = {SexHormoneType.ESTROGEN: [], SexHormoneType.PROGESTERONE: [], SexHormoneType.TESTOSTERONE: []}

        for agent in neighbors:
            if agent.uid[1] != AgentType.SEX_HORMONE:
                continue
            ht = agent.hormone_type
            if ht in found and len(found[ht]) < limits[ht]:
                found[ht].append(agent)

        # Consume found hormones
        for ht, hormones in found.items():
            for hormone in hormones:
                self.perceived_sex_hormone[ht] += 1
                self.model.remove_agent(hormone)

        return (
            self.sex_hormone_stimulation_level(SexHormoneType.ESTROGEN),
            self.sex_hormone_stimulation_level(SexHormoneType.PROGESTERONE),
            self.sex_hormone_stimulation_level(SexHormoneType.TESTOSTERONE),
        )

    def apply_hormonal_decay(self):
        """Apply decay to perceived sex hormone levels."""
        decay = self.model.weight_params.w_hormone_decay_rate
        for k in self.perceived_sex_hormone:
            self.perceived_sex_hormone[k] *= decay

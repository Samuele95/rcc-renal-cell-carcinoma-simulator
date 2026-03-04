"""TCell base class for all T cell agents.

Ported from Mesa to Repast4Py. Provides hormone perception,
TCR receptor matching (Hamming distance, hash), and sex hormone modulation.
"""
import hashlib
from abc import ABC

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
            SexHormoneType.ANDROGEN: 0
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
    def amino_to_8bit_hash(seq):
        """Convert amino acid sequence to 8-bit hash."""
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

    def perceive_sex_hormone(self, hormone_type, quantity=1, search_radius=1):
        """Perceive sex hormones in the neighborhood and accumulate their effects.

        Args:
            hormone_type: SexHormoneType string value.
            quantity: Max number of hormones to perceive.
            search_radius: Radius to search for hormones.

        Returns:
            True if hormones were perceived, False otherwise.
        """
        neighbors = grid_utils.get_neighbors_3d(
            self.model.spatial_index, self.model.grid_dims,
            self.pos, radius=search_radius, moore=True
        )
        hormones_found = []
        marker = min(quantity, 9)
        hormone_value = hormone_type.value
        for agent in neighbors:
            if len(hormones_found) >= marker:
                break
            if (agent.uid[1] == AgentType.SEX_HORMONE
                    and agent.hormone_type == hormone_value):
                hormones_found.append(agent)

        for hormone in hormones_found:
            self.perceived_sex_hormone[hormone_type] += 1
            self.model.remove_agent(hormone)

        return bool(hormones_found)

    def sex_hormone_stimulation_level(self, hormone_type):
        """Return the perceived level of a sex hormone type."""
        return self.perceived_sex_hormone[hormone_type]

    def apply_hormonal_decay(self):
        """Apply 10% decay to perceived sex hormone levels."""
        for k in self.perceived_sex_hormone:
            self.perceived_sex_hormone[k] *= 0.9

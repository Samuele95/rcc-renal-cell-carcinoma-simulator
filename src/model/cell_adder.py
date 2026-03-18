# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Cell initialization helper for the RCC model.

Provides the CellAdder class that places initial populations of immune cells,
blood vessels, and the seed tumor cell onto the 3D simulation grid.
"""
from src.agents.blood import Blood
from src.agents.tumor_cell import TumorCell

BLOOD_VESSEL_DIAMETER = 4
MIN_DISTANCE_FROM_VESSEL = 15
MAX_DISTANCE_FROM_VESSEL = 15


class CellAdder:
    """Adds cells to the initial configuration of the RCC model.

    Places immune cells at random positions, lays out a blood vessel structure
    along one edge, and seeds the initial tumor at a calculated distance from
    the vasculature.

    Attributes:
        model: The parent RCCModel instance.
        tumor_start_position: Grid coordinates where the first tumor cell is placed.
    """

    def __init__(self, model):
        """Initialize the CellAdder.

        Args:
            model: The RCCModel instance that owns this adder.
        """
        self.model = model
        self.tumor_start_position = None

    def add(self, cell_class, position=None, n=1, entry_point=False):
        """Add n agents of the given class.

        Args:
            cell_class: The agent class to instantiate.
            position: Fixed position, or None for random.
            n: Number of agents to add.
            entry_point: If True, place on grid border.
        """
        for _ in range(n):
            coords = self.model.random_position(entry_point) if position is None else position
            agent = cell_class(self.model.next_id(), self.model.rank, self.model, coords)
            self.model.add_agent(agent)

    def add_blood_vessels(self):
        """Add blood vessel cells along a cube edge."""
        w, h, d = self.model.grid_dims
        for x in range(w):
            for y in range(BLOOD_VESSEL_DIAMETER):
                for z in range(BLOOD_VESSEL_DIAMETER):
                    if not (y == 0 and (z == 0 or z == 3)) and not (y == 3 and (z == 0 or z == 3)):
                        b = Blood(self.model.next_id(), self.model.rank, self.model, (x, y, z))
                        self.model.add_agent(b)

    def calculate_tumor_start_position(self):
        """Compute a random starting position for the tumor, offset from blood vessels.

        Returns:
            Tuple of (x, y, z) grid coordinates.
        """
        w, h, d = self.model.grid_dims
        x = self.model.rng.randrange(w // 2 - w // 4, w // 2 + w // 4) if w > 4 else w // 2
        y = self.model.rng.randrange(4 + MIN_DISTANCE_FROM_VESSEL,
                               4 + MAX_DISTANCE_FROM_VESSEL + 1) if h > 4 + MAX_DISTANCE_FROM_VESSEL else h // 2
        z = self.model.rng.randrange(4 + MIN_DISTANCE_FROM_VESSEL,
                               4 + MAX_DISTANCE_FROM_VESSEL + 1) if d > 4 + MAX_DISTANCE_FROM_VESSEL else d // 2
        return (x, y, z)

    def add_single_cancer_cell(self, dna=None):
        """Create and place the initial tumor cell.

        Args:
            dna: Optional pre-built DNA sequence string. If None, a wildtype
                sequence is generated.

        Returns:
            The newly created TumorCell instance.
        """
        self.tumor_start_position = self.calculate_tumor_start_position()
        c = TumorCell(self.model.next_id(), self.model.rank, self.model,
                      pos=self.tumor_start_position, dna=dna)
        self.model.add_agent(c)
        return c

# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Measurement utility functions for converting between physical units and grid units.

Provides helpers to translate tissue volume (in litres) into discrete grid
dimensions and cell concentrations into absolute cell counts.
"""


def get_dimension_from_volume(volume: float, block_size: int = 10) -> int:
    """Convert a tissue volume to a cubic grid side length.

    Converts the volume from litres to cubic microns, takes the cube root,
    and divides by the block size to obtain the number of grid cells per axis.

    Args:
        volume: Tissue volume in litres.
        block_size: Side length of one grid voxel in microns.

    Returns:
        Grid dimension (number of voxels per axis).
    """
    micron_volume = volume * 10 ** 12
    root = (micron_volume ** (1 / 3)) / block_size
    return int(root)


def get_number_of_cells_from_concentration(cell_concentration: int, volume: float) -> int:
    """Convert a cell concentration to an absolute cell count.

    Args:
        cell_concentration: Cells per litre.
        volume: Tissue volume in litres.

    Returns:
        Number of cells to place in the simulation.
    """
    return int(cell_concentration * volume)

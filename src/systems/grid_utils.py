# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""
Grid utility functions for 3D neighbor queries.

Repast4Py's SharedGrid does not provide get_neighbors() or get_neighborhood().
Instead, the model maintains a spatial_index dict mapping (x,y,z) -> set[Agent].
These functions query that index.
"""
from functools import lru_cache


def clamp_to_grid(pos, grid_dims):
    """Clamp a position to valid grid bounds.

    Args:
        pos: (x, y, z) position tuple.
        grid_dims: (width, height, depth) tuple.

    Returns:
        Clamped (x, y, z) tuple.
    """
    w, h, d = grid_dims
    return (
        max(0, min(w - 1, pos[0])),
        max(0, min(h - 1, pos[1])),
        max(0, min(d - 1, pos[2])),
    )


@lru_cache(maxsize=32)
def _offsets_3d(radius, moore):
    """Precompute and cache offset tuples for a given (radius, moore) combination."""
    offsets = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                if not moore and abs(dx) + abs(dy) + abs(dz) > radius:
                    continue
                offsets.append((dx, dy, dz))
    return tuple(offsets)


@lru_cache(maxsize=4096)
def get_neighborhood_3d(width, height, depth, pos, radius=1, moore=True):
    """Return tuple of (x,y,z) coordinate tuples in the neighborhood of pos.

    Results are cached since the grid dimensions never change and positions
    are reused across ticks.

    Args:
        width, height, depth: Grid dimensions.
        pos: (x, y, z) center position.
        radius: Search radius.
        moore: If True, use Moore (Chebyshev) neighborhood; else Von Neumann (Manhattan).

    Returns:
        Tuple of (x, y, z) tuples excluding the center.
    """
    x, y, z = pos
    offsets = _offsets_3d(radius, moore)
    return tuple(
        (x + dx, y + dy, z + dz)
        for dx, dy, dz in offsets
        if 0 <= x + dx < width and 0 <= y + dy < height and 0 <= z + dz < depth
    )


def iter_neighbors_3d(spatial_index, grid_dims, pos, radius=1, moore=True):
    """Yield agents in the neighborhood of pos (generator, no list allocation).

    Use this when you only need the first match or will iterate once.
    """
    width, height, depth = grid_dims
    coords = get_neighborhood_3d(width, height, depth, pos, radius, moore)
    for coord in coords:
        cell_set = spatial_index.get(coord)
        if cell_set:
            yield from cell_set


def get_neighbors_3d(spatial_index, grid_dims, pos, radius=1, moore=True):
    """Return list of agents in the neighborhood of pos.

    Args:
        spatial_index: dict mapping (x,y,z) -> set[Agent]
        grid_dims: (width, height, depth) tuple
        pos: (x, y, z) center position
        radius: Search radius
        moore: If True, Moore neighborhood; else Von Neumann

    Returns:
        List of agents in the neighborhood (excluding center).
    """
    return list(iter_neighbors_3d(spatial_index, grid_dims, pos, radius, moore))


def is_in_bounds(pos, grid_dims):
    """Check if a position is within grid bounds."""
    w, h, d = grid_dims
    return 0 <= pos[0] < w and 0 <= pos[1] < h and 0 <= pos[2] < d


def is_cell_empty_3d(spatial_index, pos):
    """Check if a position has no agents.

    Args:
        spatial_index: dict mapping (x,y,z) -> set[Agent]
        pos: (x, y, z) position tuple

    Returns:
        True if no agents at position.
    """
    return not spatial_index.get(pos)


def get_empty_neighbors_3d(spatial_index, grid_dims, pos, radius=1, moore=True):
    """Return list of empty neighboring positions.

    Args:
        spatial_index: dict mapping (x,y,z) -> set[Agent]
        grid_dims: (width, height, depth) tuple
        pos: (x, y, z) center position
        radius: Search radius
        moore: If True, Moore neighborhood; else Von Neumann

    Returns:
        List of (x, y, z) tuples that have no agents.
    """
    width, height, depth = grid_dims
    coords = get_neighborhood_3d(width, height, depth, pos, radius, moore)
    return [c for c in coords if not spatial_index.get(c)]

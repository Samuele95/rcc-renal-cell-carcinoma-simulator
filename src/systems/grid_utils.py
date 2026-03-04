"""
Grid utility functions for 3D neighbor queries.

Repast4Py's SharedGrid does not provide get_neighbors() or get_neighborhood().
Instead, the model maintains a spatial_index dict mapping (x,y,z) -> set[Agent].
These functions query that index.
"""


def get_neighborhood_3d(width, height, depth, pos, radius=1, moore=True):
    """Return list of (x,y,z) coordinate tuples in the neighborhood of pos.

    Args:
        width, height, depth: Grid dimensions.
        pos: (x, y, z) center position.
        radius: Search radius.
        moore: If True, use Moore (Chebyshev) neighborhood; else Von Neumann (Manhattan).

    Returns:
        List of (x, y, z) tuples excluding the center.
    """
    x, y, z = pos
    neighborhood = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                if not moore and abs(dx) + abs(dy) + abs(dz) > radius:
                    continue
                nx, ny, nz = x + dx, y + dy, z + dz
                if 0 <= nx < width and 0 <= ny < height and 0 <= nz < depth:
                    neighborhood.append((nx, ny, nz))
    return neighborhood


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
    width, height, depth = grid_dims
    coords = get_neighborhood_3d(width, height, depth, pos, radius, moore)
    agents = []
    for coord in coords:
        agents.extend(spatial_index.get(coord, []))
    return agents


def is_cell_empty_3d(spatial_index, pos):
    """Check if a position has no agents.

    Args:
        spatial_index: dict mapping (x,y,z) -> set[Agent]
        pos: (x, y, z) position tuple

    Returns:
        True if no agents at position.
    """
    return len(spatial_index.get(pos, [])) == 0


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
    return [c for c in coords if is_cell_empty_3d(spatial_index, c)]

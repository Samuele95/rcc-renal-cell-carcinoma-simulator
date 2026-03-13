"""Sex Hormone agent — diffuses through the microenvironment."""
from enum import Enum

from src.agents.cell import Cell
from src.agents.agent_types import AgentType
from src.systems import grid_utils


class SexHormoneType(Enum):
    TESTOSTERONE = "testosterone"
    ESTROGEN = "estrogen"
    PROGESTERONE = "progesterone"


class SexHormone(Cell):
    """Sex hormone agent that diffuses through the grid with biased movement.

    Uses immediate movement (model.move_agent) instead of deferred movement
    because hormones need to diffuse each tick independently of the agent step loop.
    """

    drift_strength = 0.25

    possible_moves_1 = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (0, 1) for dz in (0, 1)]
    possible_moves_2 = [(0, 0, 1), (0, 1, 0)]

    def __init__(self, local_id, rank, model, init_pos, hormone_type):
        super().__init__(local_id, AgentType.SEX_HORMONE, rank, model, init_pos)
        self.hormone_type = hormone_type if isinstance(hormone_type, SexHormoneType) else SexHormoneType(hormone_type)

    def step(self):
        if self.pos is not None:
            if self.model.rng.random() < 0.5:
                self.diffuse()
            else:
                self.diffuse_simple()

    def diffuse(self):
        """Biased diffusion away from nearby blood vessels."""
        if self.pos is None:
            return
        w, h, d = self.model.grid_dims
        coords = grid_utils.get_neighborhood_3d(w, h, d, self.pos, radius=1, moore=True)
        if not coords:
            return

        # Local blood search (radius 3) instead of global O(B) scan
        nearby_blood = [
            a for a in grid_utils.iter_neighbors_3d(
                self.model.spatial_index, self.model.grid_dims, self.pos, radius=3, moore=True
            )
            if a.uid[1] == AgentType.BLOOD and a.pos is not None
        ]

        if not nearby_blood:
            self.model.move_agent(self, self.model.rng.choice(coords))
            return

        def dist_to_vessel(coord):
            return min(
                abs(coord[0] - v.pos[0]) + abs(coord[1] - v.pos[1]) + abs(coord[2] - v.pos[2])
                for v in nearby_blood
            )

        distances = [dist_to_vessel(c) for c in coords]
        max_d = max(distances)
        if max_d == 0:
            max_d = 1

        uniform_p = 1 / len(coords)
        probs = [
            (1 - self.drift_strength) * uniform_p + self.drift_strength * (dist / max_d) / len(coords)
            for dist in distances
        ]
        self.model.move_agent(self, self.model.rng.choices(coords, weights=probs, k=1)[0])

    def diffuse_simple(self):
        """Simple biased diffusion."""
        if self.pos is None:
            return
        if self.model.rng.random() < 0.5:
            move_delta = self.model.rng.choice(self.possible_moves_1)
        else:
            move_delta = self.model.rng.choice(self.possible_moves_2)

        new_pos = (
            self.pos[0] + move_delta[0],
            self.pos[1] + move_delta[1],
            self.pos[2] + move_delta[2]
        )

        if not grid_utils.is_in_bounds(new_pos, self.model.grid_dims):
            self.model.remove_agent(self)
        else:
            self.model.move_agent(self, new_pos)

    def save(self):
        return (self.uid, (self.pos, self.hormone_type))

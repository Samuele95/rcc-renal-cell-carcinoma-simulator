# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Base Cell class for all agents in the RCC model.

Ported from Mesa to Repast4Py. Inherits repast4py.core.Agent.
Uses model.spatial_index and grid_utils for neighbor queries.
"""
import sys
import math
from abc import ABC

from repast4py.core import Agent

from src.systems.effect import Effect, _ZERO_EFFECT
from src.systems import grid_utils


class Cell(ABC, Agent):
    """Base class for all cell agents in the grid."""

    def __init__(self, local_id, agent_type, rank, model, pos, size=1):
        """Initialize the cell.

        Args:
            local_id: Unique agent ID (from model.next_id()).
            agent_type: AgentType IntEnum value.
            rank: MPI rank.
            model: The RCCModel instance.
            pos: (x, y, z) position tuple.
            size: Diameter of the cell (default 1).
        """
        super().__init__(id=local_id, type=agent_type, rank=rank)
        self.size_diameter = size
        self.model = model
        self.pos = pos
        self._desired_pos = pos
        self.experienced_effects = model._bmi_baseline_effect.copy()
        self.search_dimension = model.cell_search_dimension
        self._alive = True

    @property
    def alive(self):
        return self._alive

    @property
    def desired_pos(self):
        return self._desired_pos

    def die(self):
        """Mark this cell as dead. Called by model.remove_agent()."""
        self._alive = False

    def base_step(self):
        """Common actions for all cells before specific behavior.

        Returns:
            True if the cell died and was removed, False otherwise.
        """
        p = self.model.weight_params.w_cell_base_death_prob
        if p <= 0.0:
            return False
        if self.model.rng.random() < p:
            self.model.remove_agent(self)
            return True
        return False

    def move(self, new_pos):
        """Set desired position (deferred movement).

        The actual grid movement happens in model.move_all_agents().
        """
        self._desired_pos = new_pos
        self.model._pending_moves.add(self)

    def move_towards(self, target_agent_type_id, look_up_size=sys.maxsize, distance=1):
        """Move towards the nearest agent of the specified type.

        Uses expanding-radius spatial index search (O(k) local) instead of
        global scan (O(N)), bounded by look_up_size. Falls back to global
        scan only if spatial search fails and look_up_size is large.

        Args:
            target_agent_type_id: AgentType int ID of target type.
            look_up_size: Maximum radius to search.
            distance: Steps to move towards target.

        Returns:
            True if moved towards a target, False otherwise.
        """
        if self.pos is None:
            return False

        x0, y0, z0 = self.pos
        grid_dims = self.model.grid_dims
        spatial_index = self.model.spatial_index

        # Expanding-radius spatial search up to look_up_size
        max_radius = min(look_up_size, max(grid_dims))
        closest_pos = None
        best_dist = float('inf')

        # Search in expanding shells: 1, 2, 4, 8, ... up to max_radius
        radius = 1
        while radius <= max_radius:
            neighbors = grid_utils.get_neighbors_3d(
                spatial_index, grid_dims, self.pos, radius=radius, moore=True
            )
            for agent in neighbors:
                if agent.uid[1] == target_agent_type_id and agent.pos is not None:
                    d = abs(agent.pos[0] - x0) + abs(agent.pos[1] - y0) + abs(agent.pos[2] - z0)
                    if d < best_dist:
                        best_dist = d
                        closest_pos = agent.pos
            if closest_pos is not None:
                break  # Found at least one target in this radius
            radius = min(radius * 2, max_radius + 1) if radius < max_radius else max_radius + 1

        if closest_pos is None:
            return False

        dx = closest_pos[0] - x0
        dy = closest_pos[1] - y0
        dz = closest_pos[2] - z0
        norm = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        if norm == 0:
            return False

        move_vector = (
            round(dx / norm * distance),
            round(dy / norm * distance),
            round(dz / norm * distance)
        )

        new_pos = grid_utils.clamp_to_grid(
            (x0 + move_vector[0], y0 + move_vector[1], z0 + move_vector[2]),
            grid_dims
        )
        self.move(new_pos)
        return True

    def find_one(self, agent_type_id, radius=1):
        """Find one agent of the specified type in the neighborhood.

        Uses generator to avoid materializing the full neighbor list.

        Args:
            agent_type_id: AgentType int ID.
            radius: Search radius.

        Returns:
            An agent of the specified type, or None.
        """
        if self.pos is None:
            return None
        for agent in grid_utils.iter_neighbors_3d(
            self.model.spatial_index, self.model.grid_dims, self.pos, radius=radius, moore=True
        ):
            if agent.uid[1] == agent_type_id:
                return agent
        return None

    def get_empty_ngbhs(self):
        """Get empty neighboring positions.

        Returns:
            List of empty (x, y, z) position tuples.
        """
        if self.pos is None:
            return []
        return grid_utils.get_empty_neighbors_3d(
            self.model.spatial_index, self.model.grid_dims, self.pos, radius=1, moore=True
        )

    # Default infiltration factor (boosted by ICI treatment)
    immune_infiltration_factor = 1

    def duplicate(self):
        """Duplicate the cell into an empty neighboring position.

        Should be overridden in subclasses for specific duplication behavior.
        """
        if self.pos is None:
            return
        empty_ngbhs = self.get_empty_ngbhs()
        if not empty_ngbhs:
            return
        new_pos = empty_ngbhs[0]
        new_cell = self.__class__(self.model.next_id(), self.model.rank, self.model, new_pos)
        self.model.add_agent(new_cell)

    def transform_into(self, agent_class, **kwargs):
        """Replace this cell with a new instance of agent_class at the same position."""
        new_agent = agent_class(self.model.next_id(), self.model.rank, self.model, self.pos, **kwargs)
        self.model.add_agent(new_agent)
        self.model.remove_agent(self)
        return new_agent

    def spawn_at_entry(self, agent_class, count=None):
        """Spawn agent_class instances at random entry points.

        Args:
            agent_class: Cell subclass to instantiate.
            count: Number to spawn (defaults to self.immune_infiltration_factor).
        """
        if count is None:
            count = self.immune_infiltration_factor
        for _ in range(count):
            pos = self.model.random_position(entry_point=True)
            agent = agent_class(self.model.next_id(), self.model.rank, self.model, pos)
            self.model.add_agent(agent)

    def consume_glucose(self, amount=None):
        """Consume glucose at the current position."""
        if self.pos is None:
            return
        if amount is None:
            amount = self.model.weight_params.w_glucose_immune_consumption
        self.model.glucose_field.consume(self.pos, amount)

    def glucose_impairment_factor(self):
        """Return glucose-based impairment multiplier (0..1) for immune activity."""
        if self.pos is None:
            return 1.0
        glucose = self.model.glucose_field.get(self.pos)
        return min(1.0, glucose * self.model.weight_params.w_glucose_immune_sensitivity)

    def try_glucose_chemotaxis(self):
        """Move towards higher glucose concentration."""
        if self.pos is None:
            return
        wp = self.model.weight_params
        if self.model.rng.random() < wp.w_glucose_chemotaxis_strength:
            dx, dy, dz = self.model.glucose_field.discretized_gradient_step(self.pos)
            if dx != 0 or dy != 0 or dz != 0:
                new_pos = grid_utils.clamp_to_grid(
                    (self.pos[0] + dx, self.pos[1] + dy, self.pos[2] + dz),
                    self.model.grid_dims
                )
                self.move(new_pos)

    def move_towards_or_chemotaxis(self, target_type_id, look_up_size=sys.maxsize):
        """Move towards target agent type, falling back to glucose chemotaxis.

        Args:
            target_type_id: AgentType int ID.
            look_up_size: Maximum radius to search.

        Returns:
            True if moved towards a target, False otherwise.
        """
        moved = self.move_towards(target_type_id, look_up_size=look_up_size)
        if not moved:
            self.try_glucose_chemotaxis()
        return moved

    def chance(self, probability):
        """Return True with the given probability."""
        return self.model.rng.random() < probability

    def try_kill_nearby(self, target_type_id, probability, radius=1):
        """Find a nearby agent of the given type and kill it with probability.

        Args:
            target_type_id: AgentType int ID of target.
            probability: Kill probability.
            radius: Search radius.

        Returns:
            The killed agent, or None.
        """
        nearby = self.find_one(target_type_id, radius=radius)
        if nearby is not None and self.chance(probability):
            self.model.remove_agent(nearby)
            self.record_kill()
            return nearby
        return None

    def move_towards_or_random_walk(self, target_type_id, look_up_size=sys.maxsize):
        """Move towards target agent type, falling back to random walk.

        Args:
            target_type_id: AgentType int ID.
            look_up_size: Maximum radius to search.

        Returns:
            True if moved towards a target, False otherwise.
        """
        moved = self.move_towards(target_type_id, look_up_size=look_up_size)
        if not moved:
            self.random_walk()
        return moved

    def random_walk(self):
        """Move to a random empty neighboring position."""
        if self.pos is None:
            return
        empty = self.get_empty_ngbhs()
        if empty:
            self.move(self.model.rng.choice(empty))

    def collect_and_apply_effects(self):
        """Collect and apply effects from neighboring cells in-place."""
        if self.pos is None:
            return
        for ngbr in grid_utils.iter_neighbors_3d(
            self.model.spatial_index, self.model.grid_dims, self.pos, radius=1, moore=True
        ):
            if ngbr.has_effect:
                self.experienced_effects.add_in_place(ngbr.get_effect())

    @staticmethod
    def sigmoid(x, k=1):
        """Sigmoid function to normalize values between 0 and 1."""
        return 1.0 / (1.0 + math.exp(-k * x))

    # Class-level flags — override in subclasses instead of trivial method overrides.
    has_effect = False
    needs_effect = False
    has_step = True

    def get_effect(self):
        """Get the effect this cell exerts on neighbors.

        Subclasses that set self._cached_effect get this behavior for free.
        """
        return getattr(self, '_cached_effect', _ZERO_EFFECT)

    def record_kill(self):
        """Record a kill by this agent type via the Observer."""
        self.model.observer.record_kill(self.uid[1])

    def save(self):
        """Save agent state for Repast4Py serialization.

        Returns:
            Tuple of (uid, state_tuple).
        """
        return (self.uid, (self.pos, self._alive))

    def step(self):
        """Agent step function. Override in subclasses."""
        ...

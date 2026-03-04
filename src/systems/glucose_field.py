"""
3D Glucose concentration field for the tumor microenvironment.

Implements:
- Diffusion via 3D discrete Laplacian (scipy.ndimage.convolve)
- Source injection from blood vessel agents
- Consumption by tumor cells (Warburg effect) and immune cells
- Gradient computation for chemotaxis
- Zero-flux (Neumann) boundary conditions via mode='nearest'
"""
import numpy as np
from scipy.ndimage import convolve

from src.agents.agent_types import AgentType


class GlucoseField:
    """3D continuous glucose concentration field overlaid on the discrete agent grid."""

    def __init__(self, width, height, depth, initial_concentration=1.0):
        """Initialize the glucose field.

        Args:
            width, height, depth: Grid dimensions (matching the agent grid).
            initial_concentration: Initial uniform glucose concentration.
        """
        self.width = width
        self.height = height
        self.depth = depth
        self.field = np.full((width, height, depth), initial_concentration, dtype=np.float64)

        # 6-connected Laplacian kernel for 3D diffusion
        self._kernel = np.zeros((3, 3, 3), dtype=np.float64)
        self._kernel[1, 1, 0] = 1.0  # z-1
        self._kernel[1, 1, 2] = 1.0  # z+1
        self._kernel[1, 0, 1] = 1.0  # y-1
        self._kernel[1, 2, 1] = 1.0  # y+1
        self._kernel[0, 1, 1] = 1.0  # x-1
        self._kernel[2, 1, 1] = 1.0  # x+1
        self._kernel[1, 1, 1] = -6.0  # center

    def get(self, pos):
        """Get glucose concentration at position (x, y, z).

        Args:
            pos: (x, y, z) tuple

        Returns:
            Glucose concentration (float).
        """
        x, y, z = pos
        return float(self.field[x, y, z])

    def consume(self, pos, amount):
        """Consume glucose at position, clamping to zero.

        Args:
            pos: (x, y, z) tuple
            amount: Amount to consume (positive).
        """
        x, y, z = pos
        self.field[x, y, z] = max(0.0, self.field[x, y, z] - amount)

    def inject(self, pos, amount):
        """Inject glucose at position (e.g., from blood vessel).

        Args:
            pos: (x, y, z) tuple
            amount: Amount to inject (positive).
        """
        x, y, z = pos
        self.field[x, y, z] += amount

    def gradient_at(self, pos):
        """Compute glucose gradient at position using central finite differences.

        Args:
            pos: (x, y, z) tuple

        Returns:
            (dC/dx, dC/dy, dC/dz) gradient tuple.
        """
        x, y, z = pos
        w, h, d = self.width, self.height, self.depth
        f = self.field

        # Central differences with clamped boundary (Neumann zero-flux)
        dx = (f[min(x + 1, w - 1), y, z] - f[max(x - 1, 0), y, z]) / 2.0
        dy = (f[x, min(y + 1, h - 1), z] - f[x, max(y - 1, 0), z]) / 2.0
        dz = (f[x, y, min(z + 1, d - 1)] - f[x, y, max(z - 1, 0)]) / 2.0

        return (dx, dy, dz)

    def discretized_gradient_step(self, pos):
        """Return the best discrete step direction following the glucose gradient.

        Useful for chemotaxis: returns a (dx, dy, dz) where each component is -1, 0, or +1.

        Args:
            pos: (x, y, z) tuple

        Returns:
            (dx, dy, dz) direction tuple, or (0, 0, 0) if gradient is zero.
        """
        gx, gy, gz = self.gradient_at(pos)

        def sign(v):
            if v > 0:
                return 1
            elif v < 0:
                return -1
            return 0

        dx, dy, dz = sign(gx), sign(gy), sign(gz)

        # Clamp to grid bounds
        x, y, z = pos
        nx = x + dx
        ny = y + dy
        nz = z + dz

        if nx < 0 or nx >= self.width:
            dx = 0
        if ny < 0 or ny >= self.height:
            dy = 0
        if nz < 0 or nz >= self.depth:
            dz = 0

        return (dx, dy, dz)

    def diffuse(self, diffusion_coeff):
        """Apply one step of 3D diffusion using the discrete Laplacian.

        Uses Neumann (zero-flux) boundary conditions via mode='nearest'.
        Stability requirement: diffusion_coeff < 1/6.

        Args:
            diffusion_coeff: Diffusion coefficient D. Must be < 1/6 for stability.
        """
        laplacian = convolve(self.field, self._kernel, mode='nearest')
        self.field += diffusion_coeff * laplacian
        np.clip(self.field, 0.0, None, out=self.field)

    def decay(self, decay_rate):
        """Apply natural glucose decay.

        Args:
            decay_rate: Fraction of glucose lost per step (0 to 1).
        """
        self.field *= (1.0 - decay_rate)

    def step(self, model):
        """Perform one simulation step of the glucose field.

        1. Blood vessels inject glucose (sources).
        2. Diffusion spreads glucose.
        3. Natural decay.

        Note: Consumption by agents is handled in their own step() methods.

        Args:
            model: The RCCModel instance (provides weight_params, spatial_index, agent lists).
        """
        wp = model.weight_params

        # 1. Source injection from blood vessels
        for agent in model.get_agents_by_type_id(AgentType.BLOOD):
            if agent.pos is not None:
                self.inject(agent.pos, wp.w_glucose_source_rate)

        # 2. Diffusion
        self.diffuse(wp.w_glucose_diffusion)

        # 3. Decay
        self.decay(wp.w_glucose_decay)

    def mean_concentration(self):
        """Return the mean glucose concentration across the field."""
        return float(np.mean(self.field))

    def total_concentration(self):
        """Return the total glucose in the field."""
        return float(np.sum(self.field))

    def min_concentration(self):
        """Return the minimum glucose concentration."""
        return float(np.min(self.field))

    def max_concentration(self):
        """Return the maximum glucose concentration."""
        return float(np.max(self.field))

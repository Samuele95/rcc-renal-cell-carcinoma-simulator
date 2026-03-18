# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

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

        # Cached blood vessel positions for vectorized injection (set by update_blood_positions)
        self._blood_xs = np.empty(0, dtype=np.intp)
        self._blood_ys = np.empty(0, dtype=np.intp)
        self._blood_zs = np.empty(0, dtype=np.intp)
        self._blood_positions_dirty = True

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

    def update_blood_positions(self, model):
        """Cache blood vessel positions as numpy arrays for vectorized injection.

        Call this when blood vessels are added or removed.
        """
        positions = [
            a.pos for a in model.iter_agents_by_type_id(AgentType.BLOOD)
            if a.pos is not None
        ]
        if positions:
            xs, ys, zs = zip(*positions)
            self._blood_xs = np.array(xs, dtype=np.intp)
            self._blood_ys = np.array(ys, dtype=np.intp)
            self._blood_zs = np.array(zs, dtype=np.intp)
        else:
            self._blood_xs = np.empty(0, dtype=np.intp)
            self._blood_ys = np.empty(0, dtype=np.intp)
            self._blood_zs = np.empty(0, dtype=np.intp)
        self._blood_positions_dirty = False

    def mark_blood_dirty(self):
        """Mark blood positions as needing refresh (call when vessels are added/removed)."""
        self._blood_positions_dirty = True

    def step(self, model):
        """Perform one simulation step of the glucose field.

        1. Blood vessels inject glucose (sources) — vectorized.
        2. Diffusion spreads glucose.
        3. Natural decay.

        Note: Consumption by agents is handled in their own step() methods.

        Args:
            model: The RCCModel instance (provides weight_params, spatial_index, agent lists).
        """
        wp = model.weight_params

        # 1. Source injection from blood vessels (vectorized)
        if self._blood_positions_dirty:
            self.update_blood_positions(model)
        if len(self._blood_xs) > 0:
            np.add.at(self.field, (self._blood_xs, self._blood_ys, self._blood_zs), wp.w_glucose_source_rate)

        # 2. Diffusion
        self.diffuse(wp.w_glucose_diffusion)

        # 3. Decay
        self.decay(wp.w_glucose_decay)

    def compute_stats(self):
        """Compute all glucose statistics in a single pass.

        Returns:
            (mean, total, min, max) tuple.
        """
        total = float(np.sum(self.field))
        size = self.field.size
        return (
            total / size,
            total,
            float(np.min(self.field)),
            float(np.max(self.field)),
        )

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

    def verify_glucose_presence(self, threshold: float = 0.01) -> dict:
        """Verify the presence of glucose molecules in the tumor microenvironment.
        
        This function addresses the professor's requirement to design a solution
        for verifying glucose presence in the microenvironment.
        
        Args:
            threshold: Minimum concentration to consider glucose "present" (default: 0.01)
            
        Returns:
            dict: Comprehensive analysis including:
                - presence_confirmed: bool indicating if glucose is present above threshold
                - coverage_percentage: % of space with detectable glucose
                - presence_map: 3D boolean array of where glucose is present
                - detection_stats: detailed statistics
        """
        presence_map = self.field >= threshold
        total_voxels = self.field.size
        present_voxels = np.sum(presence_map)
        coverage_percentage = (present_voxels / total_voxels) * 100
        
        # Additional detailed statistics
        detection_stats = {
            'threshold_used': threshold,
            'total_voxels': total_voxels,
            'voxels_above_threshold': int(present_voxels),
            'mean_in_present_regions': float(np.mean(self.field[presence_map])) if present_voxels > 0 else 0.0,
            'max_concentration': float(np.max(self.field)),
            'min_concentration': float(np.min(self.field)),
            'std_concentration': float(np.std(self.field)),
            'detection_confidence': min(1.0, coverage_percentage / 100.0)  # Confidence metric
        }
        
        return {
            'presence_confirmed': present_voxels > 0,
            'coverage_percentage': coverage_percentage,
            'presence_map': presence_map,
            'detection_stats': detection_stats
        }

    def analyze_concentration_gradient(self, position=None) -> dict:
        """Determine concentration gradients with detailed analysis.
        
        This addresses the professor's requirement to determine concentration gradients
        in the spatial microenvironment representation.
        
        Args:
            position: Specific (x,y,z) position to analyze, or None for global analysis
            
        Returns:
            dict: Comprehensive gradient analysis including:
                - gradient_magnitude: scalar magnitude of gradient
                - gradient_direction: normalized direction vector
                - gradient_vector: raw gradient components
                - local_analysis: detailed local gradient properties
                - global_analysis: field-wide gradient statistics
        """
        if position is not None:
            # Local gradient analysis at specific position
            x, y, z = position
            if not (0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth):
                raise ValueError(f"Position {position} is outside field bounds")
                
            gx, gy, gz = self.gradient_at(position)
            magnitude = np.sqrt(gx*gx + gy*gy + gz*gz)
            
            # Normalized direction (unit vector)
            if magnitude > 1e-12:
                direction = (gx/magnitude, gy/magnitude, gz/magnitude)
            else:
                direction = (0.0, 0.0, 0.0)
            
            # Local neighborhood analysis (3x3x3 around position)
            x_start, x_end = max(0, x-1), min(self.width, x+2)
            y_start, y_end = max(0, y-1), min(self.height, y+2)
            z_start, z_end = max(0, z-1), min(self.depth, z+2)
            
            local_neighborhood = self.field[x_start:x_end, y_start:y_end, z_start:z_end]
            local_analysis = {
                'neighborhood_mean': float(np.mean(local_neighborhood)),
                'neighborhood_std': float(np.std(local_neighborhood)),
                'neighborhood_range': float(np.ptp(local_neighborhood)),  # peak-to-peak
                'current_concentration': float(self.field[x, y, z]),
                'relative_to_neighborhood': 'high' if self.field[x, y, z] > np.mean(local_neighborhood) else 'low'
            }
            
            return {
                'gradient_magnitude': magnitude,
                'gradient_direction': direction,
                'gradient_vector': (gx, gy, gz),
                'local_analysis': local_analysis,
                'global_analysis': None
            }
        else:
            # Global gradient analysis across entire field
            gradients_x = np.zeros_like(self.field)
            gradients_y = np.zeros_like(self.field)
            gradients_z = np.zeros_like(self.field)
            
            # Compute gradients at all points
            for x in range(self.width):
                for y in range(self.height):
                    for z in range(self.depth):
                        gx, gy, gz = self.gradient_at((x, y, z))
                        gradients_x[x, y, z] = gx
                        gradients_y[x, y, z] = gy
                        gradients_z[x, y, z] = gz
            
            # Magnitude field
            magnitude_field = np.sqrt(gradients_x**2 + gradients_y**2 + gradients_z**2)
            
            global_analysis = {
                'mean_gradient_magnitude': float(np.mean(magnitude_field)),
                'max_gradient_magnitude': float(np.max(magnitude_field)),
                'min_gradient_magnitude': float(np.min(magnitude_field)),
                'std_gradient_magnitude': float(np.std(magnitude_field)),
                'high_gradient_regions': np.sum(magnitude_field > np.mean(magnitude_field) + np.std(magnitude_field)),
                'low_gradient_regions': np.sum(magnitude_field < np.mean(magnitude_field) - np.std(magnitude_field)),
                'gradient_uniformity': 1.0 / (1.0 + np.std(magnitude_field))  # Higher = more uniform
            }
            
            return {
                'gradient_magnitude': None,
                'gradient_direction': None,
                'gradient_vector': None,
                'local_analysis': None,
                'global_analysis': global_analysis,
                'gradient_field_x': gradients_x,
                'gradient_field_y': gradients_y,
                'gradient_field_z': gradients_z,
                'magnitude_field': magnitude_field
            }

    def find_glucose_hotspots(self, percentile_threshold: float = 90.0) -> dict:
        """Identify regions of high glucose concentration (hotspots).
        
        Args:
            percentile_threshold: Percentile above which to consider a region a hotspot
            
        Returns:
            dict: Hotspot analysis including positions and characteristics
        """
        threshold_value = np.percentile(self.field, percentile_threshold)
        hotspot_mask = self.field >= threshold_value
        hotspot_positions = np.where(hotspot_mask)
        
        if len(hotspot_positions[0]) == 0:
            return {
                'hotspots_found': False,
                'hotspot_count': 0,
                'threshold_value': threshold_value,
                'hotspot_positions': []
            }
        
        # Convert to list of (x,y,z) tuples
        hotspot_list = list(zip(hotspot_positions[0], hotspot_positions[1], hotspot_positions[2]))
        
        return {
            'hotspots_found': True,
            'hotspot_count': len(hotspot_list),
            'threshold_value': threshold_value,
            'hotspot_positions': hotspot_list,
            'mean_hotspot_concentration': float(np.mean(self.field[hotspot_mask])),
            'coverage_percentage': (len(hotspot_list) / self.field.size) * 100
        }

    def find_glucose_gradients_paths(self, start_positions: list, max_steps: int = 20) -> dict:
        """Find paths following glucose gradients from given starting positions.
        
        This can help identify how cells might move following glucose chemotaxis.
        
        Args:
            start_positions: List of (x,y,z) starting positions
            max_steps: Maximum steps to follow the gradient
            
        Returns:
            dict: Paths and analysis for each starting position
        """
        results = {}
        
        for i, start_pos in enumerate(start_positions):
            path = [start_pos]
            current_pos = start_pos
            
            for step in range(max_steps):
                # Get gradient direction
                try:
                    dx, dy, dz = self.discretized_gradient_step(current_pos)
                except (IndexError, ValueError):
                    break  # Out of bounds
                
                # If no gradient (local minimum/maximum), stop
                if dx == 0 and dy == 0 and dz == 0:
                    break
                    
                # Move to next position
                next_pos = (current_pos[0] + dx, current_pos[1] + dy, current_pos[2] + dz)
                
                # Check bounds
                if not (0 <= next_pos[0] < self.width and 
                       0 <= next_pos[1] < self.height and 
                       0 <= next_pos[2] < self.depth):
                    break
                
                path.append(next_pos)
                current_pos = next_pos
                
                # Stop if we reached a local minimum (very low gradient)
                gradient_mag = np.sqrt(sum(g*g for g in self.gradient_at(current_pos)))
                if gradient_mag < 1e-6:
                    break
            
            # Analyze path
            concentrations = [self.get(pos) for pos in path]
            results[f'path_{i}'] = {
                'start_position': start_pos,
                'path': path,
                'path_length': len(path),
                'final_position': path[-1],
                'concentrations_along_path': concentrations,
                'concentration_increase': concentrations[-1] - concentrations[0] if len(concentrations) > 1 else 0.0,
                'reached_local_optimum': len(path) < max_steps
            }
        
        return results

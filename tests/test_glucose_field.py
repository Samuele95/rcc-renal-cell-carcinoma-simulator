"""Tests for the GlucoseField system."""
import unittest
import numpy as np
from src.systems.glucose_field import GlucoseField


class TestGlucoseField(unittest.TestCase):

    def test_initialization(self):
        gf = GlucoseField(10, 10, 10, initial_concentration=5.0)
        self.assertEqual(gf.field.shape, (10, 10, 10))
        self.assertAlmostEqual(gf.get((5, 5, 5)), 5.0)

    def test_consume(self):
        gf = GlucoseField(10, 10, 10, initial_concentration=5.0)
        gf.consume((5, 5, 5), 2.0)
        self.assertAlmostEqual(gf.get((5, 5, 5)), 3.0)

    def test_consume_clamp(self):
        gf = GlucoseField(10, 10, 10, initial_concentration=1.0)
        gf.consume((5, 5, 5), 5.0)
        self.assertAlmostEqual(gf.get((5, 5, 5)), 0.0)

    def test_inject(self):
        gf = GlucoseField(10, 10, 10, initial_concentration=1.0)
        gf.inject((5, 5, 5), 3.0)
        self.assertAlmostEqual(gf.get((5, 5, 5)), 4.0)

    def test_diffusion_symmetry(self):
        """Test that diffusion from a center point is symmetric."""
        gf = GlucoseField(21, 21, 21, initial_concentration=0.0)
        gf.field[10, 10, 10] = 100.0

        gf.diffuse(0.1)

        # Check symmetry along axes
        self.assertAlmostEqual(gf.get((9, 10, 10)), gf.get((11, 10, 10)), places=10)
        self.assertAlmostEqual(gf.get((10, 9, 10)), gf.get((10, 11, 10)), places=10)
        self.assertAlmostEqual(gf.get((10, 10, 9)), gf.get((10, 10, 11)), places=10)

        # All 6 face neighbors should be equal
        neighbors = [
            gf.get((9, 10, 10)), gf.get((11, 10, 10)),
            gf.get((10, 9, 10)), gf.get((10, 11, 10)),
            gf.get((10, 10, 9)), gf.get((10, 10, 11))
        ]
        for n in neighbors:
            self.assertAlmostEqual(n, neighbors[0], places=10)

    def test_gradient_at_center(self):
        """Test gradient points from low to high concentration."""
        gf = GlucoseField(10, 10, 10, initial_concentration=0.0)
        # Set a gradient along x
        for x in range(10):
            gf.field[x, :, :] = float(x)

        dx, dy, dz = gf.gradient_at((5, 5, 5))
        self.assertGreater(dx, 0)
        self.assertAlmostEqual(dy, 0)
        self.assertAlmostEqual(dz, 0)

    def test_discretized_gradient_step(self):
        gf = GlucoseField(10, 10, 10, initial_concentration=0.0)
        for x in range(10):
            gf.field[x, :, :] = float(x)

        dx, dy, dz = gf.discretized_gradient_step((5, 5, 5))
        self.assertEqual(dx, 1)
        self.assertEqual(dy, 0)
        self.assertEqual(dz, 0)

    def test_decay(self):
        gf = GlucoseField(5, 5, 5, initial_concentration=10.0)
        gf.decay(0.1)
        self.assertAlmostEqual(gf.get((0, 0, 0)), 9.0)

    def test_statistics(self):
        gf = GlucoseField(5, 5, 5, initial_concentration=2.0)
        self.assertAlmostEqual(gf.mean_concentration(), 2.0)
        self.assertAlmostEqual(gf.total_concentration(), 2.0 * 125)
        self.assertAlmostEqual(gf.min_concentration(), 2.0)
        self.assertAlmostEqual(gf.max_concentration(), 2.0)

    def test_verify_glucose_presence(self):
        """Test glucose presence verification (Professor's requirement)."""
        gf = GlucoseField(5, 5, 5, initial_concentration=0.0)
        
        # No glucose present
        result = gf.verify_glucose_presence(threshold=0.1)
        self.assertFalse(result['presence_confirmed'])
        self.assertEqual(result['coverage_percentage'], 0.0)
        
        # Add some glucose
        gf.field[2, 2, 2] = 0.5
        gf.field[3, 3, 3] = 0.8
        
        result = gf.verify_glucose_presence(threshold=0.1)
        self.assertTrue(result['presence_confirmed'])
        self.assertGreater(result['coverage_percentage'], 0.0)
        self.assertEqual(result['detection_stats']['voxels_above_threshold'], 2)
        self.assertAlmostEqual(result['detection_stats']['max_concentration'], 0.8)

    def test_analyze_concentration_gradient_local(self):
        """Test local gradient analysis."""
        gf = GlucoseField(10, 10, 10, initial_concentration=0.0)
        
        # Create a simple gradient
        for x in range(10):
            gf.field[x, :, :] = float(x)
        
        # Test gradient analysis at specific position
        result = gf.analyze_concentration_gradient(position=(5, 5, 5))
        
        self.assertIsNotNone(result['gradient_magnitude'])
        self.assertIsNotNone(result['gradient_direction'])
        self.assertIsNotNone(result['gradient_vector'])
        self.assertIsNotNone(result['local_analysis'])
        self.assertIsNone(result['global_analysis'])
        
        # Check gradient points in positive x direction
        gx, gy, gz = result['gradient_vector']
        self.assertGreater(gx, 0)
        self.assertAlmostEqual(gy, 0)
        self.assertAlmostEqual(gz, 0)

    def test_analyze_concentration_gradient_global(self):
        """Test global gradient analysis."""
        gf = GlucoseField(5, 5, 5, initial_concentration=1.0)
        
        result = gf.analyze_concentration_gradient()
        
        self.assertIsNone(result['gradient_magnitude'])
        self.assertIsNone(result['gradient_direction'])
        self.assertIsNone(result['gradient_vector'])
        self.assertIsNone(result['local_analysis'])
        self.assertIsNotNone(result['global_analysis'])
        
        # Check that all required fields are present
        global_stats = result['global_analysis']
        required_keys = [
            'mean_gradient_magnitude', 'max_gradient_magnitude', 
            'min_gradient_magnitude', 'std_gradient_magnitude'
        ]
        for key in required_keys:
            self.assertIn(key, global_stats)

    def test_find_glucose_hotspots(self):
        """Test hotspot identification."""
        gf = GlucoseField(10, 10, 10, initial_concentration=1.0)
        
        # Add some hotspots
        gf.field[2, 2, 2] = 10.0
        gf.field[8, 8, 8] = 12.0
        
        result = gf.find_glucose_hotspots(percentile_threshold=95.0)
        
        self.assertTrue(result['hotspots_found'])
        self.assertGreater(result['hotspot_count'], 0)
        self.assertGreater(result['threshold_value'], 1.0)
        self.assertIn((2, 2, 2), result['hotspot_positions'])
        self.assertIn((8, 8, 8), result['hotspot_positions'])

    def test_find_glucose_gradients_paths(self):
        """Test gradient path following for chemotaxis."""
        gf = GlucoseField(10, 10, 10, initial_concentration=0.0)
        
        # Create a simple gradient from (0,5,5) to (9,5,5)
        for x in range(10):
            gf.field[x, 5, 5] = float(x)
        
        # Test path from low to high concentration
        start_positions = [(1, 5, 5)]
        result = gf.find_glucose_gradients_paths(start_positions, max_steps=5)
        
        self.assertIn('path_0', result)
        path_info = result['path_0']
        
        self.assertEqual(path_info['start_position'], (1, 5, 5))
        self.assertGreater(len(path_info['path']), 1)
        self.assertGreater(path_info['concentration_increase'], 0.0)

    def test_boundary_conditions(self):
        """Test gradient calculations at boundaries."""
        gf = GlucoseField(5, 5, 5, initial_concentration=1.0)
        
        # Test gradient at corner
        try:
            gradient = gf.gradient_at((0, 0, 0))
            self.assertEqual(len(gradient), 3)
        except Exception as e:
            self.fail(f"Gradient calculation at boundary failed: {e}")
        
        # Test gradient at edge
        try:
            gradient = gf.gradient_at((4, 2, 2))
            self.assertEqual(len(gradient), 3)
        except Exception as e:
            self.fail(f"Gradient calculation at edge failed: {e}")

    def test_glucose_presence_edge_cases(self):
        """Test edge cases for glucose presence detection."""
        gf = GlucoseField(3, 3, 3, initial_concentration=0.0)
        
        # Test with very small concentrations
        gf.field[1, 1, 1] = 1e-10
        
        result = gf.verify_glucose_presence(threshold=1e-9)
        self.assertTrue(result['presence_confirmed'])
        
        result = gf.verify_glucose_presence(threshold=1e-5)
        self.assertFalse(result['presence_confirmed'])


if __name__ == '__main__':
    unittest.main()

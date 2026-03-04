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


if __name__ == '__main__':
    unittest.main()

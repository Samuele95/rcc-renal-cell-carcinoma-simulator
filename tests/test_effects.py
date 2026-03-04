"""Tests for the Effect system."""
import unittest
from src.systems.effect import Effect


class TestEffect(unittest.TestCase):

    def test_default_initialization(self):
        effect = Effect()
        self.assertEqual(effect.t_kill_rate_effect, 0)
        self.assertEqual(effect.angiogenesis_effect, 0)

    def test_sum_with(self):
        e1 = Effect()
        e1.t_kill_rate_effect = 0.5
        e1.angiogenesis_effect = 0.1

        e2 = Effect()
        e2.t_kill_rate_effect = 0.3
        e2.tumour_growth_effect = 0.2

        result = e1.sum_with(e2)
        self.assertAlmostEqual(result.t_kill_rate_effect, 0.8)
        self.assertAlmostEqual(result.angiogenesis_effect, 0.1)
        self.assertAlmostEqual(result.tumour_growth_effect, 0.2)

    def test_copy(self):
        e = Effect()
        e.t_kill_rate_effect = 1.5
        e_copy = e.__copy__()
        self.assertAlmostEqual(e_copy.t_kill_rate_effect, 1.5)
        e_copy.t_kill_rate_effect = 0
        self.assertAlmostEqual(e.t_kill_rate_effect, 1.5)


if __name__ == '__main__':
    unittest.main()

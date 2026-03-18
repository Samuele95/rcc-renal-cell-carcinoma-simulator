# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Tests for the Effect system."""
import unittest
from src.systems.effect import Effect


class TestEffect(unittest.TestCase):

    def test_default_initialization(self):
        effect = Effect()
        self.assertEqual(effect.t_kill_rate_effect, 0)
        self.assertEqual(effect.angiogenesis_effect, 0)

    def test_add_in_place(self):
        e1 = Effect()
        e1.t_kill_rate_effect = 0.5
        e1.angiogenesis_effect = 0.1

        e2 = Effect()
        e2.t_kill_rate_effect = 0.3
        e2.tumour_growth_effect = 0.2

        e1.add_in_place(e2)
        self.assertAlmostEqual(e1.t_kill_rate_effect, 0.8)
        self.assertAlmostEqual(e1.angiogenesis_effect, 0.1)
        self.assertAlmostEqual(e1.tumour_growth_effect, 0.2)

    def test_all_slots_initialized(self):
        """All slots should be initialized to 0."""
        effect = Effect()
        for attr in Effect.__slots__:
            self.assertEqual(getattr(effect, attr), 0)


if __name__ == '__main__':
    unittest.main()

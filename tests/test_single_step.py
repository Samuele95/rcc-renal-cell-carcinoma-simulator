# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Integration test: minimal model runs without crashing."""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestSingleStep(unittest.TestCase):

    def test_model_creation(self):
        """Test that the model can be created with default parameters."""
        from mpi4py import MPI
        from src.model.rcc_model import RCCModel

        model = RCCModel(comm=MPI.COMM_SELF, volume=0.0001, max_steps=10)
        self.assertTrue(model.running)
        self.assertEqual(model.steps, 0)
        self.assertGreater(len(model._all_agents), 0)

    def test_single_step(self):
        """Test that the model can execute a single step."""
        from mpi4py import MPI
        from src.model.rcc_model import RCCModel

        model = RCCModel(comm=MPI.COMM_SELF, volume=0.0001, max_steps=10)
        initial_count = len(model._all_agents)
        model.step()
        self.assertEqual(model.steps, 1)
        # Agents should still exist
        self.assertGreater(len(model._all_agents), 0)

    def test_ten_steps(self):
        """Test that the model survives 10 steps."""
        from mpi4py import MPI
        from src.model.rcc_model import RCCModel

        model = RCCModel(comm=MPI.COMM_SELF, volume=0.0001, max_steps=10)
        for _ in range(10):
            if model.running:
                model.step()
        self.assertGreater(model.steps, 0)
        self.assertGreater(len(model.data_log), 0)

    def test_glucose_field_evolves(self):
        """Test that the glucose field changes over steps."""
        from mpi4py import MPI
        from src.model.rcc_model import RCCModel

        model = RCCModel(comm=MPI.COMM_SELF, volume=0.0001, max_steps=10)
        initial_mean = model.glucose_field.mean_concentration()
        model.step()
        # After a step with blood vessels injecting glucose, field should change
        new_mean = model.glucose_field.mean_concentration()
        # The glucose field should have changed (sources inject, diffusion, decay)
        self.assertNotAlmostEqual(initial_mean, new_mean, places=5)


if __name__ == '__main__':
    unittest.main()

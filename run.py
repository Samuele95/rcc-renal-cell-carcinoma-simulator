"""Entry point for the RCC Repast4Py simulation.

Run: mpirun -n 1 python run.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mpi4py import MPI
from repast4py import schedule

from src.model.rcc_model import RCCModel


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    # Create model with default parameters (or load from config)
    model = RCCModel(comm=comm)

    if rank == 0:
        print(f"RCC Model initialized: grid={model.grid_dims}, "
              f"sex={model.sex}, treatment={model.patient_params.treatment}")
        print(f"Initial agents: {len(model._all_agents)}")

    # Create schedule runner
    runner = schedule.init_schedule_runner(comm)
    runner.schedule_repeating_event(1, 1, model.step)
    runner.schedule_stop(model.max_steps)
    runner.schedule_end_event(model.log_data)

    # Execute simulation
    runner.execute()

    if rank == 0:
        print(f"\nSimulation complete after {model.steps} steps.")
        print(f"Survival: {model.survival}")
        print(f"Final tumor cells: {model.count_agents(0)}")
        print(f"Data written to logs/simulation_log.csv")


if __name__ == '__main__':
    main()

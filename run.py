"""Entry point for the RCC Repast4Py simulation.

Usage:
    mpirun -n 1 python run.py                          # defaults
    mpirun -n 1 python run.py --config my_params.yaml  # custom config
    mpirun -n 1 python run.py --sex M --bmi 28 --seed 42 --plot
    mpirun -n 1 python run.py --treatment TKI --max-steps 300
"""
import argparse
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mpi4py import MPI
from repast4py import schedule

from src.model.rcc_model import RCCModel
from src.agents.agent_types import AgentType


def load_yaml_config(path):
    """Load a YAML config file and flatten sections into a single dict."""
    import yaml
    with open(path) as f:
        raw = yaml.safe_load(f)
    flat = {}
    for section in raw.values():
        if isinstance(section, dict):
            flat.update(section)
    return flat


def parse_args():
    parser = argparse.ArgumentParser(
        description="RCC Tumor Microenvironment Simulation (Repast4Py)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  mpirun -n 1 python run.py --sex M --bmi 28\n"
               "  mpirun -n 1 python run.py --config my_config.yaml --plot\n"
               "  mpirun -n 1 python run.py --treatment ICI --max-steps 300 --seed 42\n"
    )

    parser.add_argument("--config", "-c", default="config/default_params.yaml",
                        help="Path to YAML config file (default: config/default_params.yaml)")
    parser.add_argument("--seed", type=int, help="Random seed (overrides config)")
    parser.add_argument("--max-steps", type=int, help="Maximum simulation steps (overrides config)")
    parser.add_argument("--sex", choices=["F", "M"], help="Patient sex (overrides config)")
    parser.add_argument("--bmi", type=float, help="Patient BMI (overrides config)")
    parser.add_argument("--treatment", choices=["None", "ICI", "TKI", "ICI+TKI"],
                        help="Treatment type (overrides config)")
    parser.add_argument("--treatment-start", type=int, help="Step to start treatment (overrides config)")
    parser.add_argument("--volume", type=float, help="Simulation volume in mL (overrides config)")
    parser.add_argument("--plot", action="store_true",
                        help="Generate plots after simulation completes")
    parser.add_argument("--progress", type=int, default=50, metavar="N",
                        help="Print progress every N steps (0 to disable, default: 50)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress all output except errors")
    parser.add_argument("--snapshot", type=int, default=0, metavar="N",
                        help="Save environment snapshots every N steps (0 to disable)")
    parser.add_argument("--ui", action="store_true",
                        help="Launch the Streamlit web interface instead of running simulation")

    return parser.parse_args()


def build_params(args):
    """Build kwargs dict from YAML config + CLI overrides."""
    # Load YAML config
    params = {}
    if os.path.exists(args.config):
        params = load_yaml_config(args.config)
    elif args.config != "config/default_params.yaml":
        print(f"Warning: Config file '{args.config}' not found, using defaults.", file=sys.stderr)

    # CLI overrides
    if args.seed is not None:
        params["random_seed"] = args.seed
    if args.max_steps is not None:
        params["max_steps"] = args.max_steps
    if args.sex is not None:
        params["sex"] = args.sex
    if args.bmi is not None:
        params["BMI"] = args.bmi
    if args.treatment is not None:
        params["treatment"] = args.treatment
    if args.treatment_start is not None:
        params["treatment_start"] = args.treatment_start
    if args.volume is not None:
        params["volume"] = args.volume

    return params


def print_header(model):
    """Print simulation configuration summary."""
    pp = model.patient_params
    mp = model.model_params
    w, h, d = model.grid_dims
    print("=" * 60)
    print("  RCC Tumor Microenvironment Simulation")
    print("=" * 60)
    print(f"  Grid:        {w}x{h}x{d}  (volume={mp.volume} mL)")
    print(f"  Patient:     sex={pp.sex}, BMI={pp.BMI}")
    print(f"  Treatment:   {pp.treatment} (starts step {pp.treatment_start})")
    print(f"  Seed:        {mp.random_seed}")
    print(f"  Max steps:   {mp.max_steps}")
    print(f"  Agents:      {model.total_agent_count}")
    print(f"    Tumor:     {model.count_agents(AgentType.TUMOR_CELL)}")
    print(f"    Immune:    {model.count_agents(AgentType.CD8_CYTOTOXIC_T_CELL) + model.count_agents(AgentType.NATURAL_KILLER) + model.count_agents(AgentType.MACROPHAGE_M1) + model.count_agents(AgentType.MACROPHAGE_M2) + model.count_agents(AgentType.DENDRITIC_CELL) + model.count_agents(AgentType.NEUTROPHIL)}")
    print("-" * 60)


def print_progress(model):
    """Print a compact progress line."""
    n_tumor = model.count_agents(AgentType.TUMOR_CELL)
    n_total = model.total_agent_count
    glucose = model.glucose_field.mean_concentration()
    print(f"  Step {model.steps:>4d}/{model.max_steps}  |  "
          f"tumor={n_tumor:<5d}  agents={n_total:<6d}  glucose={glucose:.2f}")


def print_summary(model, elapsed):
    """Print end-of-simulation summary."""
    n_tumor = model.count_agents(AgentType.TUMOR_CELL)
    print()
    print("=" * 60)
    print("  Simulation Complete")
    print("=" * 60)
    print(f"  Steps:       {model.steps}")
    print(f"  Elapsed:     {elapsed:.1f}s ({elapsed / max(1, model.steps):.2f}s/step)")
    print(f"  Outcome:     {'SURVIVAL' if model.survival else 'TUMOR PROGRESSION'}")
    print(f"  Tumor cells: {n_tumor}")
    print(f"  Total kills: {model.observer.total_kills()}")
    print(f"    CTC:       {model.observer.cytotoxic_T_cell_kills}")
    print(f"    NK:        {model.observer.nkl_kill_count}")
    print(f"    M1:        {model.observer.m1_macrophage_kills}")
    print(f"    DC:        {model.observer.dendritic_cell_kills}")
    print(f"    PDC:       {model.observer.pdc_kills}")
    print(f"    Neutro:    {model.observer.neutrophil_kills}")
    print(f"  Log:         logs/simulation_log.csv")
    print("-" * 60)


def main():
    args = parse_args()
    
    # Launch Streamlit UI if --ui flag is provided
    if args.ui:
        import subprocess
        import os
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "app.py")
        if os.path.exists(ui_path):
            try:
                subprocess.run(["streamlit", "run", ui_path], check=True)
            except subprocess.CalledProcessError:
                print("Error: Failed to launch Streamlit. Make sure streamlit is installed:")
                print("  pip install streamlit")
            except FileNotFoundError:
                print("Error: Streamlit not found. Install it with:")
                print("  pip install streamlit")
        else:
            print(f"Error: UI file not found at {ui_path}")
        return
    
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    params = build_params(args)
    model = RCCModel(comm=comm, **params)

    quiet = args.quiet or rank != 0

    if not quiet:
        print_header(model)

    # Snapshot setup
    snapshot_dir = None
    if args.snapshot > 0:
        config_parent = os.path.dirname(os.path.abspath(args.config))
        snapshot_dir = os.path.join(config_parent, "snapshots") if "runs" in config_parent else os.path.join("logs", "snapshots")

    # Wrap model.step with progress reporting
    progress_interval = args.progress
    start_time = time.time()

    original_step = model.step

    def step_with_progress():
        original_step()
        if not quiet and progress_interval > 0 and model.steps % progress_interval == 0:
            print_progress(model)
        if snapshot_dir and model.steps % args.snapshot == 0:
            model.save_snapshot(snapshot_dir)

    # Create schedule runner
    runner = schedule.init_schedule_runner(comm)
    runner.schedule_repeating_event(1, 1, step_with_progress)
    runner.schedule_stop(model.max_steps)
    runner.schedule_end_event(model.log_data)

    # Execute
    runner.execute()

    # Save final snapshot
    if snapshot_dir:
        model.save_snapshot(snapshot_dir)

    elapsed = time.time() - start_time

    if not quiet:
        print_summary(model, elapsed)

    # Auto-plot
    if args.plot and rank == 0:
        try:
            from src.visualization.plot_results import plot_population_dynamics
            from src.visualization.plot_glucose import plot_glucose_timeseries
            plot_population_dynamics()
            plot_glucose_timeseries()
        except Exception as e:
            print(f"Warning: Could not generate plots: {e}", file=sys.stderr)


if __name__ == '__main__':
    main()

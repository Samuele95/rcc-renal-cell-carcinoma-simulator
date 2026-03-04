"""Post-hoc visualization of simulation results.

Usage:
    python -m src.visualization.plot_results                        # defaults
    python -m src.visualization.plot_results logs/run1.csv -o run1  # custom
"""
import argparse
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


def plot_population_dynamics(csv_path="logs/simulation_log.csv", output_dir="plots"):
    """Plot cell population time series from simulation log."""
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(csv_path)

    # Cell population counts
    non_cell_cols = {
        'step', 'apoptosis_count', 'm1_kills', 'dc_kills', 'pdc_kills',
        'ctc_kills', 'nkl_kills', 'neutrophil_kills',
        'mean_glucose', 'total_glucose', 'min_glucose', 'max_glucose',
    }
    cell_cols = [c for c in df.columns if c not in non_cell_cols]

    fig, ax = plt.subplots(figsize=(14, 8))
    for col in cell_cols:
        ax.plot(df['step'], df[col], label=col.replace('_', ' ').title())
    ax.set_xlabel('Step')
    ax.set_ylabel('Count')
    ax.set_title('Cell Population Dynamics')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'population_dynamics.png'), dpi=300)
    plt.close()

    # Tumor cell focus
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df['step'], df['tumor_cells'], 'r-', linewidth=2, label='Tumor Cells')
    ax.fill_between(df['step'], df['tumor_cells'], alpha=0.2, color='red')
    ax.set_xlabel('Step')
    ax.set_ylabel('Tumor Cell Count')
    ax.set_title('Tumor Growth Over Time')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'tumor_growth.png'), dpi=300)
    plt.close()

    # Kill counts
    kill_cols = ['apoptosis_count', 'm1_kills', 'dc_kills', 'pdc_kills', 'ctc_kills', 'nkl_kills', 'neutrophil_kills']
    existing_kill_cols = [c for c in kill_cols if c in df.columns]
    if existing_kill_cols:
        fig, ax = plt.subplots(figsize=(10, 6))
        for col in existing_kill_cols:
            ax.plot(df['step'], df[col], label=col.replace('_', ' ').title())
        ax.set_xlabel('Step')
        ax.set_ylabel('Cumulative Kills')
        ax.set_title('Kill Counts Over Time')
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'kill_counts.png'), dpi=300)
        plt.close()

    print(f"Plots saved to {output_dir}/")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Plot RCC simulation results")
    parser.add_argument("csv", nargs="?", default="logs/simulation_log.csv",
                        help="Path to simulation CSV log (default: logs/simulation_log.csv)")
    parser.add_argument("-o", "--output-dir", default="plots",
                        help="Output directory for plots (default: plots)")
    args = parser.parse_args()
    plot_population_dynamics(args.csv, args.output_dir)

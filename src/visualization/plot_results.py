"""Post-hoc visualization of simulation results.

Reads simulation_log.csv and generates population time series and kill count plots.
"""
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt


def plot_population_dynamics(csv_path="logs/simulation_log.csv", output_dir="plots"):
    """Plot cell population time series from simulation log."""
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(csv_path)

    # Cell population counts
    cell_cols = [c for c in df.columns if c not in [
        'step', 'apoptosis_count', 'm1_kills', 'dc_kills', 'pdc_kills',
        'ctc_kills', 'nkl_kills', 'mean_glucose', 'total_glucose',
        'min_glucose', 'max_glucose'
    ]]

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
    kill_cols = ['apoptosis_count', 'm1_kills', 'dc_kills', 'pdc_kills', 'ctc_kills', 'nkl_kills']
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
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "logs/simulation_log.csv"
    plot_population_dynamics(csv_path)

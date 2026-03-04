"""Glucose field visualization.

Usage:
    python -m src.visualization.plot_glucose                        # defaults
    python -m src.visualization.plot_glucose logs/run1.csv -o run1  # custom
"""
import argparse
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


def plot_glucose_timeseries(csv_path="logs/simulation_log.csv", output_dir="plots"):
    """Plot glucose statistics over time from simulation log."""
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(csv_path)

    glucose_cols = ['mean_glucose', 'total_glucose', 'min_glucose', 'max_glucose']
    existing = [c for c in glucose_cols if c in df.columns]

    if not existing:
        print("No glucose data found in log.")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Glucose Field Statistics Over Time', fontsize=14)

    for ax, col in zip(axes.flat, existing):
        ax.plot(df['step'], df[col], 'b-', linewidth=1.5)
        ax.set_xlabel('Step')
        ax.set_ylabel(col.replace('_', ' ').title())
        ax.set_title(col.replace('_', ' ').title())
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'glucose_timeseries.png'), dpi=300)
    plt.close()
    print(f"Glucose plots saved to {output_dir}/")


def plot_glucose_field_slice(field_3d, slice_axis='z', slice_index=None, output_path="plots/glucose_slice.png"):
    """Plot a 2D slice of the 3D glucose field as a heatmap.

    Args:
        field_3d: numpy array of shape (W, H, D)
        slice_axis: 'x', 'y', or 'z' axis to slice through
        slice_index: Index along the slice axis (default: middle)
        output_path: Where to save the plot
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if slice_index is None:
        slice_index = field_3d.shape[{'x': 0, 'y': 1, 'z': 2}[slice_axis]] // 2

    if slice_axis == 'z':
        data = field_3d[:, :, slice_index]
        xlabel, ylabel = 'X', 'Y'
    elif slice_axis == 'y':
        data = field_3d[:, slice_index, :]
        xlabel, ylabel = 'X', 'Z'
    else:
        data = field_3d[slice_index, :, :]
        xlabel, ylabel = 'Y', 'Z'

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(data.T, origin='lower', cmap='YlOrRd', aspect='equal')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f'Glucose Concentration ({slice_axis}={slice_index})')
    plt.colorbar(im, ax=ax, label='Glucose')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_glucose_gradient(field_3d, slice_z=None, output_path="plots/glucose_gradient.png"):
    """Plot glucose gradient vectors on a z-slice."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if slice_z is None:
        slice_z = field_3d.shape[2] // 2

    data = field_3d[:, :, slice_z]
    gy, gx = np.gradient(data)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.imshow(data.T, origin='lower', cmap='YlOrRd', alpha=0.5)

    step = max(1, data.shape[0] // 20)
    Y, X = np.mgrid[0:data.shape[0]:step, 0:data.shape[1]:step]
    U = gx[::step, ::step]
    V = gy[::step, ::step]
    ax.quiver(X, Y, U, V, color='blue', alpha=0.7)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title(f'Glucose Gradient Vectors (z={slice_z})')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Plot glucose field statistics")
    parser.add_argument("csv", nargs="?", default="logs/simulation_log.csv",
                        help="Path to simulation CSV log (default: logs/simulation_log.csv)")
    parser.add_argument("-o", "--output-dir", default="plots",
                        help="Output directory for plots (default: plots)")
    args = parser.parse_args()
    plot_glucose_timeseries(args.csv, args.output_dir)

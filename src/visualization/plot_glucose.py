# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

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
    """Plot mean, total, min, and max glucose over time.

    Args:
        csv_path: Path to the simulation CSV log.
        output_dir: Directory to save glucose_timeseries.png.
    """
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
    """Plot glucose gradient vectors overlaid on a z-slice heatmap.

    Args:
        field_3d: 3D numpy array of glucose concentrations (W, H, D).
        slice_z: Z-index to slice at (default: middle).
        output_path: File path for the saved plot.
    """
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


def plot_glucose_presence_analysis(glucose_field, threshold=0.01, output_dir="plots"):
    """Plot glucose presence verification: presence map, threshold overlay, stats, and histogram.

    Args:
        glucose_field: GlucoseField instance with a ``verify_glucose_presence`` method.
        threshold: Minimum concentration considered "present".
        output_dir: Directory to save glucose_presence_analysis.png.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Get presence analysis
    presence_analysis = glucose_field.verify_glucose_presence(threshold)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Glucose Presence Analysis (threshold={threshold})', fontsize=14)
    
    # Plot presence map (z-slice)
    z_slice = glucose_field.depth // 2
    presence_slice = presence_analysis['presence_map'][:, :, z_slice]
    concentration_slice = glucose_field.field[:, :, z_slice]
    
    # Presence/absence map
    axes[0,0].imshow(presence_slice.T, origin='lower', cmap='RdYlBu_r', aspect='equal')
    axes[0,0].set_title(f'Glucose Presence Map (z={z_slice})')
    axes[0,0].set_xlabel('X')
    axes[0,0].set_ylabel('Y')
    
    # Concentration with threshold overlay
    im = axes[0,1].imshow(concentration_slice.T, origin='lower', cmap='YlOrRd', aspect='equal')
    axes[0,1].contour(concentration_slice.T, levels=[threshold], colors='blue', linewidths=2)
    axes[0,1].set_title(f'Concentration with Threshold (blue line)')
    axes[0,1].set_xlabel('X')
    axes[0,1].set_ylabel('Y')
    plt.colorbar(im, ax=axes[0,1], label='Glucose Concentration')
    
    # Statistics text
    stats = presence_analysis['detection_stats']
    stats_text = f"""Detection Statistics:
Coverage: {presence_analysis['coverage_percentage']:.1f}%
Voxels above threshold: {stats['voxels_above_threshold']}
Mean in present regions: {stats['mean_in_present_regions']:.3f}
Detection confidence: {stats['detection_confidence']:.3f}
Max concentration: {stats['max_concentration']:.3f}
Standard deviation: {stats['std_concentration']:.3f}"""
    
    axes[1,0].text(0.05, 0.95, stats_text, transform=axes[1,0].transAxes, 
                   fontsize=10, verticalalignment='top', fontfamily='monospace')
    axes[1,0].set_xlim(0, 1)
    axes[1,0].set_ylim(0, 1)
    axes[1,0].axis('off')
    axes[1,0].set_title('Detection Statistics')
    
    # Coverage histogram
    flat_concentrations = glucose_field.field.flatten()
    axes[1,1].hist(flat_concentrations, bins=50, alpha=0.7, density=True, color='skyblue')
    axes[1,1].axvline(threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold={threshold}')
    axes[1,1].set_xlabel('Glucose Concentration')
    axes[1,1].set_ylabel('Probability Density')
    axes[1,1].set_title('Concentration Distribution')
    axes[1,1].legend()
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'glucose_presence_analysis.png'), dpi=300)
    plt.close()


def plot_glucose_gradient_analysis(glucose_field, output_dir="plots", slice_z=None):
    """Plot a 6-panel gradient analysis: concentration, magnitude, vectors, X/Y components, and stats.

    Args:
        glucose_field: GlucoseField instance with ``analyze_concentration_gradient``.
        output_dir: Directory to save glucose_gradient_analysis.png.
        slice_z: Z-index to visualize (default: middle).
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if slice_z is None:
        slice_z = glucose_field.depth // 2
    
    # Get global gradient analysis
    gradient_analysis = glucose_field.analyze_concentration_gradient()
    
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle(f'Glucose Gradient Analysis (z={slice_z})', fontsize=16)
    
    # Extract gradient data for the slice
    gx_slice = gradient_analysis['gradient_field_x'][:, :, slice_z]
    gy_slice = gradient_analysis['gradient_field_y'][:, :, slice_z]
    gz_slice = gradient_analysis['gradient_field_z'][:, :, slice_z]
    magnitude_slice = gradient_analysis['magnitude_field'][:, :, slice_z]
    concentration_slice = glucose_field.field[:, :, slice_z]
    
    # Concentration field
    im0 = axes[0,0].imshow(concentration_slice.T, origin='lower', cmap='YlOrRd', aspect='equal')
    axes[0,0].set_title('Glucose Concentration')
    axes[0,0].set_xlabel('X')
    axes[0,0].set_ylabel('Y')
    plt.colorbar(im0, ax=axes[0,0], label='Concentration')
    
    # Gradient magnitude
    im1 = axes[0,1].imshow(magnitude_slice.T, origin='lower', cmap='viridis', aspect='equal')
    axes[0,1].set_title('Gradient Magnitude')
    axes[0,1].set_xlabel('X')
    axes[0,1].set_ylabel('Y')
    plt.colorbar(im1, ax=axes[0,1], label='|∇C|')
    
    # Gradient vectors overlay
    step = max(1, glucose_field.width // 15)
    Y, X = np.mgrid[0:glucose_field.width:step, 0:glucose_field.height:step]
    U = gx_slice[::step, ::step]
    V = gy_slice[::step, ::step]
    
    axes[0,2].imshow(concentration_slice.T, origin='lower', cmap='YlOrRd', alpha=0.6, aspect='equal')
    axes[0,2].quiver(X, Y, U, V, magnitude_slice[::step, ::step], scale=None, alpha=0.8, cmap='plasma')
    axes[0,2].set_title('Gradient Vector Field')
    axes[0,2].set_xlabel('X')
    axes[0,2].set_ylabel('Y')
    
    # Gradient X component
    im2 = axes[1,0].imshow(gx_slice.T, origin='lower', cmap='RdBu', aspect='equal')
    axes[1,0].set_title('Gradient X-component')
    axes[1,0].set_xlabel('X')
    axes[1,0].set_ylabel('Y')
    plt.colorbar(im2, ax=axes[1,0], label='∂C/∂x')
    
    # Gradient Y component
    im3 = axes[1,1].imshow(gy_slice.T, origin='lower', cmap='RdBu', aspect='equal')
    axes[1,1].set_title('Gradient Y-component')
    axes[1,1].set_xlabel('X')
    axes[1,1].set_ylabel('Y')
    plt.colorbar(im3, ax=axes[1,1], label='∂C/∂y')
    
    # Statistics
    global_stats = gradient_analysis['global_analysis']
    stats_text = f"""Global Gradient Statistics:
Mean magnitude: {global_stats['mean_gradient_magnitude']:.4f}
Max magnitude: {global_stats['max_gradient_magnitude']:.4f}
Std magnitude: {global_stats['std_gradient_magnitude']:.4f}
High gradient regions: {global_stats['high_gradient_regions']}
Low gradient regions: {global_stats['low_gradient_regions']}
Uniformity index: {global_stats['gradient_uniformity']:.3f}"""
    
    axes[1,2].text(0.05, 0.95, stats_text, transform=axes[1,2].transAxes,
                   fontsize=10, verticalalignment='top', fontfamily='monospace')
    axes[1,2].set_xlim(0, 1)
    axes[1,2].set_ylim(0, 1)
    axes[1,2].axis('off')
    axes[1,2].set_title('Gradient Statistics')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'glucose_gradient_analysis.png'), dpi=300)
    plt.close()


def plot_glucose_hotspots(glucose_field, percentile=90, output_dir="plots"):
    """Plot glucose hotspot positions (3D scatter), slice overlay, and statistics.

    Args:
        glucose_field: GlucoseField instance with ``find_glucose_hotspots``.
        percentile: Percentile threshold defining a hotspot (default: 90).
        output_dir: Directory to save glucose_hotspots.png.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    hotspots = glucose_field.find_glucose_hotspots(percentile)
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(f'Glucose Hotspots Analysis ({percentile}th percentile)', fontsize=14)
    
    # 3D visualization of hotspots
    if hotspots['hotspots_found']:
        hotspot_positions = np.array(hotspots['hotspot_positions'])
        ax = fig.add_subplot(131, projection='3d')
        fig.delaxes(axes[0])  # Remove the 2D axis
        ax = fig.add_subplot(131, projection='3d')
        
        scatter = ax.scatter(hotspot_positions[:, 0], hotspot_positions[:, 1], hotspot_positions[:, 2],
                           c=[glucose_field.get(tuple(pos)) for pos in hotspot_positions],
                           cmap='YlOrRd', alpha=0.7)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('Hotspot Positions (3D)')
        plt.colorbar(scatter, ax=ax, shrink=0.5)
    else:
        axes[0].text(0.5, 0.5, 'No hotspots found', ha='center', va='center', transform=axes[0].transAxes)
        axes[0].set_title('Hotspot Positions (3D)')
        axes[0].axis('off')
    
    # Slice view with hotspots
    z_slice = glucose_field.depth // 2
    concentration_slice = glucose_field.field[:, :, z_slice]
    
    im = axes[1].imshow(concentration_slice.T, origin='lower', cmap='YlOrRd', aspect='equal')
    
    if hotspots['hotspots_found']:
        # Mark hotspots in this slice
        slice_hotspots = [pos for pos in hotspots['hotspot_positions'] if pos[2] == z_slice]
        if slice_hotspots:
            hotspot_x, hotspot_y = zip(*[(pos[0], pos[1]) for pos in slice_hotspots])
            axes[1].scatter(hotspot_x, hotspot_y, c='blue', marker='x', s=50, alpha=0.8)
    
    axes[1].axhline(y=hotspots['threshold_value'], color='white', linestyle='--', alpha=0.7)
    axes[1].set_title(f'Hotspots in Slice (z={z_slice})')
    axes[1].set_xlabel('X')
    axes[1].set_ylabel('Y')
    plt.colorbar(im, ax=axes[1], label='Concentration')
    
    # Statistics
    if hotspots['hotspots_found']:
        stats_text = f"""Hotspot Statistics:
Threshold value: {hotspots['threshold_value']:.3f}
Hotspot count: {hotspots['hotspot_count']}
Coverage: {hotspots['coverage_percentage']:.2f}%
Mean concentration: {hotspots['mean_hotspot_concentration']:.3f}"""
    else:
        stats_text = f"""Hotspot Statistics:
Threshold value: {hotspots['threshold_value']:.3f}
Hotspot count: 0
Coverage: 0.00%
No hotspots detected above threshold"""
    
    axes[2].text(0.05, 0.95, stats_text, transform=axes[2].transAxes,
                fontsize=12, verticalalignment='top', fontfamily='monospace')
    axes[2].set_xlim(0, 1)
    axes[2].set_ylim(0, 1)
    axes[2].axis('off')
    axes[2].set_title('Hotspot Statistics')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'glucose_hotspots.png'), dpi=300)
    plt.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Plot glucose field statistics")
    parser.add_argument("csv", nargs="?", default="logs/simulation_log.csv",
                        help="Path to simulation CSV log (default: logs/simulation_log.csv)")
    parser.add_argument("-o", "--output-dir", default="plots",
                        help="Output directory for plots (default: plots)")
    args = parser.parse_args()
    plot_glucose_timeseries(args.csv, args.output_dir)

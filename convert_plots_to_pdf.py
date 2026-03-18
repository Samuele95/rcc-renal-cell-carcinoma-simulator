#!/usr/bin/env python3

# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Convert simulation plots to PDF format for LaTeX inclusion."""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd

def convert_png_to_pdf(png_path, pdf_path):
    """Convert a PNG image to PDF."""
    img = mpimg.imread(png_path)
    
    # Create figure with appropriate size
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.imshow(img)
    ax.axis('off')
    plt.tight_layout(pad=0)
    
    # Save as PDF
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', pad_inches=0, dpi=300)
    plt.close()
    print(f"Converted {png_path} -> {pdf_path}")

def create_publication_figures():
    """Create publication-quality figures from simulation data."""
    
    # Read simulation data
    df = pd.read_csv('logs/simulation_log.csv')
    output_dir = 'docs/report/figures'
    
    # 1. Population dynamics plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Define important cell types and their colors
    important_cells = {
        'tumor_cells': ('Tumor Cells', 'red', '-'),
        'cytotoxic_t_cells': ('Cytotoxic T Cells', 'blue', '-'),
        'cd8_naive_t_cells': ('CD8+ Naive', 'lightblue', '--'),
        'cd4_naive_t_cells': ('CD4+ Naive', 'cyan', '--'),
        'macrophage_m1': ('M1 Macrophages', 'green', '-'),
        'macrophage_m2': ('M2 Macrophages', 'orange', '-'),
        'natural_killers': ('Natural Killers', 'purple', '-'),
        'dendritic_cells': ('Dendritic Cells', 'brown', '-'),
        'regulatory_t_cells': ('Regulatory T Cells', 'gray', '-')
    }
    
    for col, (label, color, style) in important_cells.items():
        if col in df.columns:
            ax.plot(df['step'], df[col], label=label, color=color, linestyle=style, linewidth=2)
    
    ax.set_xlabel('Simulation Step', fontsize=14)
    ax.set_ylabel('Cell Count', fontsize=14)
    ax.set_title('Population Dynamics in RCC Tumor Microenvironment', fontsize=16, fontweight='bold')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=12)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/population_dynamics.pdf', format='pdf', bbox_inches='tight', dpi=300)
    plt.close()
    
    # 2. Tumor growth focus
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df['step'], df['tumor_cells'], 'r-', linewidth=3, label='Tumor Cells')
    ax.fill_between(df['step'], df['tumor_cells'], alpha=0.3, color='red')
    ax.set_xlabel('Simulation Step', fontsize=14)
    ax.set_ylabel('Tumor Cell Count', fontsize=14)
    ax.set_title('Tumor Growth Over Time', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/tumor_growth.pdf', format='pdf', bbox_inches='tight', dpi=300)
    plt.close()
    
    # 3. Glucose dynamics
    glucose_cols = ['mean_glucose', 'min_glucose', 'max_glucose']
    existing_glucose = [c for c in glucose_cols if c in df.columns]
    
    if existing_glucose:
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['blue', 'green', 'red']
        labels = ['Mean', 'Minimum', 'Maximum']
        
        for i, col in enumerate(existing_glucose):
            ax.plot(df['step'], df[col], color=colors[i % len(colors)], 
                   linewidth=2, label=f'{labels[i % len(labels)]} Glucose')
        
        ax.set_xlabel('Simulation Step', fontsize=14)
        ax.set_ylabel('Glucose Concentration', fontsize=14)
        ax.set_title('Glucose Field Dynamics', fontsize=16, fontweight='bold')
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/glucose_dynamics.pdf', format='pdf', bbox_inches='tight', dpi=300)
        plt.close()
    
    # 4. Kill statistics
    kill_cols = ['ctc_kills', 'nkl_kills', 'm1_kills', 'dc_kills', 'pdc_kills', 'neutrophil_kills']
    existing_kills = [c for c in kill_cols if c in df.columns]
    
    if existing_kills:
        # Get total kills for each type
        kill_totals = {col.replace('_kills', ''): df[col].iloc[-1] for col in existing_kills}
        
        fig, ax = plt.subplots(figsize=(10, 6))
        agents = list(kill_totals.keys())
        counts = list(kill_totals.values())
        colors = plt.cm.Set3(np.linspace(0, 1, len(agents)))
        
        bars = ax.bar(agents, counts, color=colors)
        ax.set_xlabel('Agent Type', fontsize=14)
        ax.set_ylabel('Total Kills', fontsize=14)
        ax.set_title('Total Tumor Cell Kills by Agent Type', fontsize=16, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            if count > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                       int(count), ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/kill_statistics.pdf', format='pdf', bbox_inches='tight', dpi=300)
        plt.close()
    
    print("Generated publication-quality figures in docs/report/figures/")

if __name__ == "__main__":
    os.chdir('/media/talino/data/MASL/rcc_repast4py')
    
    # Convert existing PNG plots to PDF
    plot_files = ['population_dynamics.png', 'tumor_growth.png', 'glucose_timeseries.png', 'kill_counts.png']
    
    for png_file in plot_files:
        png_path = f'plots/{png_file}'
        pdf_path = f'docs/report/figures/{png_file.replace(".png", ".pdf")}'
        
        if os.path.exists(png_path):
            convert_png_to_pdf(png_path, pdf_path)
    
    # Create additional publication figures
    create_publication_figures()
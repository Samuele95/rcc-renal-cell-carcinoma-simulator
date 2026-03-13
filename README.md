# RCC Tumor Microenvironment Simulation

An agent-based model of renal cell carcinoma (kidney cancer) that simulates the battle between tumor cells and the immune system in 3D tissue.

![Simulation Preview](docs/screenshots/simulation_preview.png) *(Screenshot placeholder)*

## 🎯 What Does This Simulate?

This tool models a small piece of kidney tissue as a 3D grid where:
- **🔴 Tumor cells** try to grow, divide, and evade immune detection
- **🔵 Immune cells** (T-cells, NK cells, macrophages, etc.) hunt and destroy tumor cells  
- **🩸 Blood vessels** supply glucose (energy) to all cells
- **💊 Treatment drugs** boost the immune system's ability to fight

**Two possible outcomes:**
- **✅ Survival** — Immune system eliminates all tumor cells
- **❌ Progression** — Tumor grows beyond 2,000+ cells

## 🚀 Quick Start

### Prerequisites

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt install python3-dev libopenmpi-dev

# Or on macOS with Homebrew
brew install open-mpi
```

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd rcc_repast4py

# Install Python dependencies  
pip install -r requirements.txt

# Alternative: Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Usage Options

#### 1. 🖥️ Web UI (Recommended)
```bash
# Launch the Streamlit web interface
python run.py --ui

# Or directly:
streamlit run ui/app.py
```
Then open your browser to http://localhost:8501

#### 2. 🔧 Command Line
```bash
# Run with defaults
mpirun -n 1 python run.py

# Customize parameters
mpirun -n 1 python run.py --sex M --bmi 28 --treatment ICI --max-steps 300

# Use custom config file
mpirun -n 1 python run.py --config my_config.yaml --plot
```

#### 3. ⚙️ Configuration File
```yaml
# my_config.yaml
patient:
  sex: "F"
  BMI: 25.0
  treatment: "ICI+TKI" 
  treatment_start: 50

simulation:
  max_steps: 200
  random_seed: 42
  volume: 0.000008
```

## 📊 Understanding Results

### Treatment Options
- **None** — Natural immunity only (control)
- **ICI** — Immunotherapy (blocks PD-1/PD-L1 checkpoints) 
- **TKI** — Targeted therapy (cuts off tumor blood supply)
- **ICI+TKI** — Combination therapy (strongest option)

### Key Metrics
- **Tumor Growth** — How fast the red mass expands
- **Immune Kills** — Which cell types are most effective
- **Glucose Levels** — Energy distribution in the tissue
- **Cell Populations** — Balance of tumor vs immune cells over time

### 3D Visualization
The simulator shows:
- Red dots = Tumor cells
- Blue/Purple dots = Immune cells  
- Green dots = Blood vessels
- The tissue can be rotated and zoomed in the 3D view

## 🧬 Model Details

### Cell Types (18 total)
- **Tumor**: Cancerous cells that grow and divide
- **CD8 T-cells**: Primary tumor killers
- **NK cells**: Innate immune response
- **Macrophages**: M1 (anti-tumor) vs M2 (pro-tumor)
- **Dendritic cells**: Activate other immune cells
- **Regulatory T-cells**: Suppress immune response
- **Helper T-cells**: Coordinate immune response
- **Neutrophils**: Early inflammatory response
- **Mast cells**: Release inflammatory signals
- **Adipocytes**: Fat cells (affect immune function)

### Key Biological Processes
- **Angiogenesis**: Tumor-driven blood vessel formation
- **Glucose metabolism**: Warburg effect modeling
- **Immune checkpoints**: PD-1/PD-L1 inhibition
- **Sex hormone effects**: BMI and hormonal influences
- **Cell movement**: Chemotaxis and random walk

### Spatial Structure
- 3D cubic grid (dimensions depend on tissue volume)
- Each voxel can contain multiple cells
- Glucose diffusion across neighboring voxels
- Cell movement limited to adjacent voxels

## 🔬 Research Applications

This model is designed for:
- **Treatment comparison**: Which therapy works best for which patient?
- **Biomarker discovery**: What immune patterns predict success?
- **Combination therapy**: How do ICI + TKI interact?
- **Patient stratification**: BMI, sex, and immune status effects
- **Educational demos**: Visualizing tumor-immune dynamics

## 📁 Project Structure

```
rcc_repast4py/
├── README.md                    # This file
├── run.py                       # CLI entry point
├── requirements.txt             # Dependencies
├── config/
│   └── default_params.yaml     # Default simulation parameters
├── src/
│   ├── model/
│   │   └── rcc_model.py        # Main simulation engine
│   ├── agents/                  # Cell type definitions
│   └── visualization/           # Plotting utilities
├── ui/                          # Streamlit web interface
│   ├── app.py                  # Main UI entry point
│   ├── pages/                  # UI pages (home, configure, run, results, etc.)
│   └── lib/                    # UI support functions
├── logs/                        # Simulation outputs
└── tests/                       # Unit tests
```

## 🎛️ Parameters

### Patient Parameters
- `sex`: "F" or "M" (affects hormone levels)
- `BMI`: Body mass index (higher BMI weakens immune response)
- `treatment`: "None", "ICI", "TKI", or "ICI+TKI"
- `treatment_start`: Step when treatment begins

### Simulation Parameters  
- `max_steps`: Maximum simulation duration
- `random_seed`: For reproducible results
- `volume`: Tissue size in mL (affects grid dimensions)
- Cell concentrations for 11 immune cell types
- 80+ biological weight parameters for fine-tuning

## 🧪 Examples

### Compare Treatments
```bash
# Female, BMI 22, no treatment
mpirun -n 1 python run.py --sex F --bmi 22 --treatment None --seed 1

# Same patient with immunotherapy
mpirun -n 1 python run.py --sex F --bmi 22 --treatment ICI --seed 1

# Same patient with combination therapy  
mpirun -n 1 python run.py --sex F --bmi 22 --treatment ICI+TKI --seed 1
```

### Study BMI Effects
```bash
# Normal weight
mpirun -n 1 python run.py --bmi 22 --treatment ICI --seed 1

# Overweight  
mpirun -n 1 python run.py --bmi 28 --treatment ICI --seed 1

# Obese
mpirun -n 1 python run.py --bmi 35 --treatment ICI --seed 1
```

## 🐛 Troubleshooting

### Import Errors
```bash
# If you see "ModuleNotFoundError: No module named 'mpi4py'"
pip install mpi4py

# If you see MPI compilation errors:
# Ubuntu/Debian:
sudo apt install libopenmpi-dev python3-dev

# macOS:
brew install open-mpi
export MPICC=/opt/homebrew/bin/mpicc  # if needed
```

### Performance Issues
- Use smaller tissue volumes for faster runs
- Reduce `max_steps` for quicker testing
- Disable snapshots (`--snapshot 0`) for speed
- Use fewer immune cell types in custom configs

### Memory Issues
- Reduce grid dimensions by lowering `volume`
- Increase system swap space
- Run on a machine with more RAM

## 📚 References

1. **Repast4Py**: Agent-based modeling framework
   - https://repast.github.io/repast4py.site/
2. **Kidney Cancer Biology**: RCC tumor microenvironment  
3. **Immunotherapy**: PD-1/PD-L1 checkpoint inhibition
4. **Targeted Therapy**: Angiogenesis inhibition

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎓 Citation

If you use this simulator in research, please cite:

```bibtex
@software{rcc_simulation_2024,
  title = {RCC Tumor Microenvironment Simulation},
  author = {[Author Name]},
  year = {2024},
  url = {[Repository URL]}
}
```

---

**For questions or support, please open an issue or contact [contact@email.com]**
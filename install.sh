#!/bin/bash
# Non-interactive installer for the RCC Tumor Microenvironment Simulator.
# Creates a virtual environment, installs all dependencies, and verifies the setup.
#
# Usage:
#   chmod +x install.sh
#   ./install.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "  [*] $1"; }
ok()      { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "  ${YELLOW}[!!]${NC} $1"; }
fail()    { echo -e "  ${RED}[FAIL]${NC} $1"; exit 1; }

echo ""
echo "  RCC Tumor Microenvironment Simulator — Installer"
echo "  ================================================="
echo ""

# ── 1. Python 3.10+ ────────────────────────────────────────────────
info "Checking Python version..."
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        ver=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        major=$("$candidate" -c "import sys; print(sys.version_info.major)")
        minor=$("$candidate" -c "import sys; print(sys.version_info.minor)")
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    fail "Python 3.10+ is required but not found. Install it first."
fi
ok "Found $PYTHON $ver"

# ── 2. MPI ──────────────────────────────────────────────────────────
info "Checking MPI installation..."
if command -v mpirun >/dev/null 2>&1; then
    mpi_ver=$(mpirun --version 2>&1 | head -1)
    ok "MPI found: $mpi_ver"
else
    warn "MPI (mpirun) not found. The simulation engine requires MPI."
    echo "       Ubuntu/Debian : sudo apt install libopenmpi-dev"
    echo "       CentOS/RHEL   : sudo yum install openmpi-devel"
    echo "       macOS (brew)  : brew install open-mpi"
    echo ""
    echo "  Continuing anyway — you can install MPI later."
fi

# ── 3. Virtual environment ──────────────────────────────────────────
info "Setting up virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    $PYTHON -m venv .venv
    ok "Created .venv"
else
    ok ".venv already exists"
fi

# shellcheck disable=SC1091
source .venv/bin/activate
ok "Activated .venv ($(python --version))"

# ── 4. Dependencies ─────────────────────────────────────────────────
info "Installing Python dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
ok "All dependencies installed"

# ── 5. Import verification ──────────────────────────────────────────
info "Verifying imports..."
if python test_imports.py; then
    ok "All imports verified"
else
    warn "Some imports failed — check the output above."
fi

# ── 6. Done ─────────────────────────────────────────────────────────
echo ""
echo "  ================================================="
echo "  Installation complete!"
echo "  ================================================="
echo ""
echo "  Activate the environment:"
echo "    source .venv/bin/activate"
echo ""
echo "  Launch the web UI:"
echo "    streamlit run ui/app.py"
echo ""
echo "  Or run from the command line:"
echo "    mpirun -n 1 python run.py --sex F --bmi 25 --treatment ICI --plot"
echo ""
echo "  Run tests:"
echo "    python -m pytest tests/ -v"
echo ""

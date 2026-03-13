#!/bin/bash
# Quick setup and demo launcher for RCC Simulation

set -e  # Exit on any error

echo "🔬 RCC Tumor Simulation - Quick Setup & Demo Launcher"
echo "====================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Python 3
print_info "Checking Python 3..."
if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
print_success "Python $PYTHON_VERSION found"

# Check system dependencies for mpi4py
print_info "Checking system dependencies..."
if command_exists dpkg; then
    # Debian/Ubuntu
    if ! dpkg -l | grep -q libopenmpi-dev; then
        print_warning "libopenmpi-dev not found. Installing..."
        if [[ $EUID -eq 0 ]]; then
            apt update && apt install -y python3-dev libopenmpi-dev
        else
            echo "🔐 Need sudo to install system dependencies:"
            sudo apt update && sudo apt install -y python3-dev libopenmpi-dev
        fi
        print_success "System dependencies installed"
    else
        print_success "System dependencies already installed"
    fi
elif command_exists brew; then
    # macOS with Homebrew
    if ! brew list open-mpi >/dev/null 2>&1; then
        print_warning "open-mpi not found. Installing..."
        brew install open-mpi
        print_success "open-mpi installed"
    else
        print_success "open-mpi already installed"
    fi
else
    print_warning "Cannot auto-install MPI dependencies. Please ensure MPI is installed:"
    echo "  Ubuntu/Debian: sudo apt install python3-dev libopenmpi-dev"
    echo "  CentOS/RHEL:   sudo yum install python3-devel openmpi-devel"
    echo "  macOS:         brew install open-mpi"
fi

# Create virtual environment if it doesn't exist
print_info "Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    print_info "Creating new virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source .venv/bin/activate
print_success "Virtual environment activated"

# Install/update requirements
print_info "Installing/updating Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Dependencies installed"

# Verify Streamlit installation
print_info "Verifying Streamlit installation..."
if python -c "import streamlit" 2>/dev/null; then
    print_success "Streamlit is available"
else
    print_error "Streamlit installation failed"
    exit 1
fi

# Quick syntax check for UI files
print_info "Running syntax check on UI files..."
python3 -m py_compile ui/app.py
for page_file in ui/pages/*.py; do
    python3 -m py_compile "$page_file"
done
print_success "All UI files have valid Python syntax"

echo ""
echo "🎉 Setup complete! Choose what to do:"
echo ""
echo "1) 🖥️  Launch Streamlit Web UI (Recommended)"
echo "2) 💻 Run CLI simulation"
echo "3) 🧪 Run tests"
echo "4) 📊 View existing results"
echo "5) 🚪 Exit"
echo ""

while true; do
    read -p "Enter your choice (1-5): " choice
    case $choice in
        1)
            print_info "Starting Streamlit Web UI..."
            echo "🌐 Open your browser to: http://localhost:8501"
            echo "Press Ctrl+C to stop the server"
            streamlit run ui/app.py
            break
            ;;
        2)
            print_info "Running CLI simulation with default parameters..."
            python run.py
            break
            ;;
        3)
            print_info "Running test suite..."
            python -m pytest tests/ -v
            break
            ;;
        4)
            print_info "Checking for existing results..."
            if [ -d "plots" ] && [ "$(ls -A plots)" ]; then
                echo "📊 Results found in plots/ directory:"
                ls -la plots/
            else
                echo "No results found. Run a simulation first!"
            fi
            break
            ;;
        5)
            print_info "Goodbye!"
            break
            ;;
        *)
            print_warning "Invalid choice. Please enter 1-5."
            ;;
    esac
done
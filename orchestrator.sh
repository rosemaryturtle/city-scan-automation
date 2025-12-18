#!/usr/bin/env bash
set -e

echo "======================================"
echo "    Cityscan Orchestrator (Setup)"
echo "======================================"

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"

###########################################
# 1. Enforce Python 3.11 via pyenv
###########################################

if ! command -v pyenv &>/dev/null; then
    echo "ERROR: pyenv is required but not installed."
    exit 1
fi

if [ ! -f ".python-version" ]; then
    echo "ERROR: .python-version file not found."
    exit 1
fi

PYENV_PYTHON_VERSION=$(cat .python-version)

echo "Required Python version: $PYENV_PYTHON_VERSION"

# Ensure version is installed
if ! pyenv versions --bare | grep -q "^${PYENV_PYTHON_VERSION}$"; then
    echo "ERROR: Python $PYENV_PYTHON_VERSION not installed."
    echo "Run: pyenv install $PYENV_PYTHON_VERSION"
    exit 1
fi

# Activate pyenv local version explicitly
export PYENV_VERSION="$PYENV_PYTHON_VERSION"
PYTHON_BIN="$(pyenv which python)"

echo "Using Python interpreter: $PYTHON_BIN"

# Hard version check
PYTHON_MAJOR_MINOR=$("$PYTHON_BIN" - <<EOF
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
EOF
)

if [[ "$PYTHON_MAJOR_MINOR" != "3.11" ]]; then
    echo "ERROR: Python 3.11 required, got $PYTHON_MAJOR_MINOR"
    exit 1
fi

###########################################
# 2. Remove old venv
###########################################
if [ -d "venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf venv
fi

###########################################
# 3. Create new virtual environment
###########################################
echo "Creating new virtual environment..."
"$PYTHON_BIN" -m venv venv

echo "Activating venv..."
source venv/bin/activate

###########################################
# 4. Install dependencies
###########################################
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "ERROR: requirements.txt not found!"
    exit 1
fi

###########################################
# 5. Register Jupyter kernel
###########################################
echo "Registering Jupyter kernel..."

if jupyter kernelspec list 2>/dev/null | grep -q "cityscan"; then
    jupyter kernelspec remove -f cityscan
fi

python -m ipykernel install \
  --user \
  --name cityscan \
  --display-name "Cityscan (Python 3.11)"

echo "======================================"
echo "Setup complete."
echo "Python locked to 3.11"
echo "Use kernel: Cityscan (Python 3.11)"
echo "======================================"

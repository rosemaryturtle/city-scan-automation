#!/usr/bin/env bash
set -e

echo "======================================"
echo "    Cityscan Orchestrator (Setup)"
echo "======================================"

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"

###########################################
# 1. Select Python interpreter
###########################################

# Prefer pyenv local Python if available
if command -v pyenv &>/dev/null; then
    echo "pyenv detected."

    # Ensure local version is installed
    PYENV_PYTHON_VERSION=$(cat .python-version 2>/dev/null || true)

    if [ -n "$PYENV_PYTHON_VERSION" ]; then
        echo "pyenv local version: $PYENV_PYTHON_VERSION"

        # Find python executable
        PYTHON_BIN=$(pyenv which python 2>/dev/null || true)

        if [[ "$PYTHON_BIN" == *"$PYENV_PYTHON_VERSION"* ]]; then
            echo "Using pyenv Python: $PYTHON_BIN"
        else
            echo "ERROR: pyenv Python version not installed."
            echo "Run: pyenv install $PYENV_PYTHON_VERSION"
            exit 1
        fi
    fi
fi

# Fallback if pyenv isn't used
if [ -z "$PYTHON_BIN" ]; then
    echo "pyenv not used. Falling back to system python3."
    PYTHON_BIN=$(command -v python3)
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: No suitable Python 3 installed."
    exit 1
fi

echo "Python interpreter: $PYTHON_BIN"

###########################################
# 2. Remove old venv safely
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
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "ERROR: requirements.txt not found!"
    exit 1
fi

###########################################
# 5. Register Jupyter kernel cleanly
###########################################
echo "Registering Jupyter kernel..."

# Remove old kernel if exists
if jupyter kernelspec list 2>/dev/null | grep -q "cityscan"; then
    jupyter kernelspec remove -f cityscan
fi

python -m ipykernel install --user --name cityscan --display-name "Cityscan (Python 3.11)"

echo "======================================"
echo "Setup complete."
echo "Use kernel: Cityscan (Python 3.11)"
echo "======================================"

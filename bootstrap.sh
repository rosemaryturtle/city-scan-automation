#!/usr/bin/env bash
set -e

echo "======================================"
echo " Cityscan Bootstrap (Python Runtime)"
echo "======================================"

OS="$(uname -s)"

###########################################
# macOS
###########################################
if [[ "$OS" == "Darwin" ]]; then
    echo "Detected macOS"

    if ! command -v brew &>/dev/null; then
        echo "Homebrew not found. Installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    echo "Installing system dependencies..."
    brew install \
        pyenv \
        openssl \
        readline \
        sqlite3 \
        xz \
        zlib \
        tcl-tk

###########################################
# Linux (Ubuntu/Debian)
###########################################
elif [[ "$OS" == "Linux" ]]; then
    echo "Detected Linux"

    sudo apt update
    sudo apt install -y \
        build-essential \
        curl \
        git \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        libffi-dev \
        liblzma-dev \
        tk-dev \
        pyenv

else
    echo "Unsupported OS: $OS"
    exit 1
fi

###########################################
# pyenv setup
###########################################
if ! command -v pyenv &>/dev/null; then
    echo "ERROR: pyenv installation failed."
    exit 1
fi

PYTHON_VERSION="3.11.8"

echo "Installing Python $PYTHON_VERSION via pyenv..."
pyenv install -s "$PYTHON_VERSION"

echo "Setting local Python version..."
pyenv local "$PYTHON_VERSION"

echo "======================================"
echo "Bootstrap complete."
echo "Run: bash orchestrator.sh"
echo "======================================"

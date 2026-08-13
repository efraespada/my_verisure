#!/bin/bash
# Setup script for My Verisure CLI

echo "🚀 Setting up My Verisure CLI..."

VENV_DIR=".ha-2026.8-venv"
PYTHON_BIN="python3.14"

# Check if the supported virtual environment exists
if [ ! -d "${VENV_DIR}" ]; then
    echo "📦 Creating Home Assistant 2026.8.1 virtual environment..."
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements-dev.txt

# Make CLI executable
echo "🔨 Making CLI executable..."
chmod +x my_verisure_cli.py

# Create symlink (optional)
echo "🔗 Creating symlink to /usr/local/bin/my_verisure (requires sudo)..."
echo "You can run: sudo ln -s $(pwd)/my_verisure_cli.py /usr/local/bin/my_verisure"

echo "✅ Setup complete!"
echo ""
echo "Usage:"
echo "  source ${VENV_DIR}/bin/activate"
echo "  python my_verisure_cli.py --help"
echo ""
echo "Or with symlink:"
echo "  my_verisure --help"

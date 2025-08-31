#!/bin/bash
# Setup script for My Verisure CLI

echo "🚀 Setting up My Verisure CLI..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Make CLI executable
echo "🔨 Making CLI executable..."
chmod +x my_verisure_cli.py

# Create symlink (optional)
echo "🔗 Creating symlink to /usr/local/bin/my_verisure (requires sudo)..."
echo "You can run: sudo ln -s $(pwd)/my_verisure_cli.py /usr/local/bin/my_verisure"

echo "✅ Setup complete!"
echo ""
echo "Usage:"
echo "  source venv/bin/activate"
echo "  python my_verisure_cli.py --help"
echo ""
echo "Or with symlink:"
echo "  my_verisure --help"

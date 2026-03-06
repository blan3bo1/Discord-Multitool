#!/bin/bash

# Discord Quest Helper Installation Script

echo "📦 Installing Discord Quest Helper..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$python_version < 3.9" | bc -l) )); then
    echo "❌ Python 3.9+ is required (found $python_version)"
    exit 1
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create config directory
mkdir -p ~/.discord_quest_helper

# Copy default config if not exists
if [ ! -f ~/.discord_quest_helper/config.json ]; then
    cp config.json ~/.discord_quest_helper/config.json
fi

echo "✅ Installation complete!"
echo ""
echo "To run the helper:"
echo "  1. Make sure Discord is closed"
echo "  2. Run: python main.py"
echo ""
echo "To build standalone app:"
echo "  ./scripts/build_macos.sh"
#!/bin/bash
cd "$(dirname "$0")" || exit

echo "============================================="
echo " 🛠️ Environment Setup Check (macOS)"
echo "============================================="

# 1. If venv exists, exit immediately
if [ -d "system/venv" ]; then
    echo "[INFO] Virtual environment already exists."
    echo "[INFO] No further action required."
    echo "============================================="
    exit 0
fi

# 2. If not, create and install
echo "[INFO] Environment not found. Starting installation..."
python3.11 -m venv system/venv
source system/venv/bin/activate
pip install --upgrade pip
pip install selenium requests PyQt6 pyinstaller google-generativeai

echo "✅ Setup complete."
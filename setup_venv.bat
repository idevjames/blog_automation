#!/bin/bash
cd "$(dirname "$0")"

echo "============================================="
echo "  Standard Environment Setup (macOS)"
echo "============================================="

# 1. Create virtual environment if not exists
if [ -d "system/venv" ]; then
    echo "[INFO] venv already exists."
else
    echo "[INFO] Creating new venv..."
    python3 -m venv system/venv
fi

# 2. Define paths (Mac uses 'bin' folder)
PYTHON_PATH="./system/venv/bin/python3"
PIP_PATH="./system/venv/bin/pip3"

echo "[INFO] Upgrading pip..."
$PYTHON_PATH -m pip install --upgrade pip

echo "[INFO] Installing libraries (google-genai)..."
$PIP_PATH install selenium requests PyQt6 pyinstaller google-genai

echo "============================================="
echo "[OK] Setup complete!"
echo "============================================="
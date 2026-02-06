@echo off
setlocal
cd /d "%~dp0"

echo =============================================
echo   Windows Python Environment Setup
echo =============================================

if exist "system\venv" (
    echo [INFO] Virtual environment already exists.
) else (
    echo [INFO] Creating new virtual environment...
    python -m venv system\venv
)

set "PYTHON_PATH=system\venv\Scripts\python.exe"
set "PIP_PATH=system\venv\Scripts\pip.exe"

secho [INFO] Upgrading pip...
"%PYTHON_PATH%" -m pip install --upgrade pip

echo [INFO] Installing libraries...
"%PIP_PATH%" install selenium requests PyQt6 pyinstaller google-genai webdriver-manager

echo =============================================
echo [OK] Setup Complete!
echo =============================================

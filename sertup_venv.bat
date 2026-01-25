@echo off
cd /d "%~dp0"

echo =============================================
echo  🛠️ Environment Setup Check (Windows)
echo =============================================

:: 1. If venv exists, exit immediately
if exist "system\venv" (
    echo [INFO] Virtual environment already exists.
    echo [INFO] No further action required.
    goto :END
)

:: 2. If not, create and install
echo [INFO] Environment not found. Starting installation...
python -m venv system\venv
call system\venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install selenium requests PyQt6 pyinstaller google-generativeai
echo [OK] Setup complete.

:END
echo =============================================
pause
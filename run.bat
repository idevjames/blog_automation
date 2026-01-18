@echo off
cd /d "%~dp0"

echo =============================================
echo  Blog Automation Bot Launcher
echo =============================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    goto InstallPython
) else (
    goto CheckSystem
)

:InstallPython
echo [!] Python is not installed.
echo [!] Trying to install Python 3.11 automatically...
echo.

winget install -e --id Python.Python.3.11 --scope machine

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Automatic installation failed.
    echo Please install Python manually from: https://www.python.org/downloads/
    echo (Make sure to check 'Add Python to PATH' during installation)
    pause
    exit
)

echo.
echo [OK] Python installed successfully.
echo [INFO] Please close this window and run 'run.bat' again to apply changes.
pause
exit

:CheckSystem
if not exist "system" (
    echo [ERROR] 'system' folder not found.
    pause
    exit
)

if not exist "system\venv" (
    echo [INIT] Setting up virtual environment...
    python -m venv system\venv
    call system\venv\Scripts\activate.bat
    pip install --upgrade pip
    pip install selenium requests
    echo [OK] Setup complete.
) else (
    call system\venv\Scripts\activate.bat
)

set PYTHONPATH=%PYTHONPATH%;%cd%

if exist "system\gui_main.py" (
    echo [START] Running the bot...
    echo ---------------------------------------------
    python system\gui_main.py
) else (
    echo [ERROR] system\gui_main.py not found.
)

echo.
echo Program finished.
pause
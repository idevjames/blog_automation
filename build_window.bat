@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================================
echo     NAVER BLOG AUTOMATION BUILD START (WINDOWS)
echo ========================================================

:: 1. Check and Activate Virtual Environment
set "VENV_PATH=%~dp0system\venv\Scripts\activate.bat"

if exist "%VENV_PATH%" (
    echo Activating virtual environment...
    call "%VENV_PATH%"
) else (
    echo [ERROR] Virtual environment not found at: "%VENV_PATH%"
    pause
    exit /b 1
)

:: 2. Install Dependencies
echo Checking dependencies...
python -m pip install --upgrade pip
pip install PyQt6 selenium pyinstaller google-generativeai

:: 3. Clean Previous Build Files
echo Cleaning old files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

:: 4. Run PyInstaller
:: [Note] Removed --add-data for settings to keep it external
echo Running PyInstaller...
python -m PyInstaller --noconfirm --onedir --windowed --clean ^
 --add-data "system\bot_class;bot_class" ^
 --add-data "system\ai_helper.py;." ^
 --collect-submodules "bot_class" ^
 "system\gui_main.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [BUILD FAILED] Check the errors above.
    pause
    exit /b 1
)

:: 5. Configure External Settings Folder
echo Finalizing...
if not exist "dist\gui_main\settings" mkdir "dist\gui_main\settings"

:: [Note] Copy all txt files, then delete setup_gemini.txt to protect personal API key
copy "system\settings\*.txt" "dist\gui_main\settings\" >nul
if exist "dist\gui_main\settings\setup_gemini.txt" del /f /q "dist\gui_main\settings\setup_gemini.txt"

echo [SUCCESS] Configuration completed excluding setup_gemini.txt

echo.
echo ========================================================
echo     SUCCESSFULLY COMPLETED!
echo ========================================================
start explorer dist
pause
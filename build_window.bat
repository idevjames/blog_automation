@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo    Naver Blog Bot Build Process (Windows)
echo ================================================

:: 1. Environment Check
if not exist "system\venv" (
    echo [WARN] Environment not found. Checking setup_venv...
    if exist "setup_venv.bat" (
        call setup_venv.bat
    ) else (
        echo [ERROR] setup_venv.bat not found. Please set up venv first.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Environment (system/venv) detected. Skipping setup.
)

:: 2. Activate Virtual Environment
if exist "system\venv\Scripts\activate.bat" (
    echo [INFO] Activating system/venv environment...
    call system\venv\Scripts\activate.bat
) else (
    echo [ERROR] Critical Error: Cannot find system\venv\Scripts\activate.bat!
    pause
    exit /b 1
)

:: 3. Check Build Tools
echo [INFO] Checking build tools...
python -m pip install --upgrade pip >nul 2>&1
pip install pyinstaller >nul 2>&1

:: 4. Clean up previous build
echo [INFO] Cleaning up previous build (build, dist, spec)...
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist NaverBlogBot.spec del NaverBlogBot.spec

:: 5. Run PyInstaller
echo [INFO] Starting PyInstaller build process...

:: [IMPORTANT] Windows uses semicolon (;) for --add-data separator
python -m PyInstaller --noconfirm --onedir --windowed --clean ^
    --name "NaverBlogBot" ^
    --add-data "system/bot_class;bot_class" ^
    "system/gui_main.py"

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller failed.
    pause
    exit /b 1
)

:: 6. Organize 'user_data' folder
echo [INFO] Organizing 'user_data' folder for distribution...

set "DIST_USER_DATA=dist\user_data"

:: (1) Create skeleton folders
if not exist "%DIST_USER_DATA%\settings" mkdir "%DIST_USER_DATA%\settings"
if not exist "%DIST_USER_DATA%\naver_profile" mkdir "%DIST_USER_DATA%\naver_profile"

:: (2) Copy default settings
if exist "system\settings" (
    echo [INFO] Copying default settings from 'system/settings'...
    xcopy /y /q "system\settings\*.txt" "%DIST_USER_DATA%\settings\"
) else if exist "user_data\settings" (
    echo [INFO] Copying default settings from 'user_data/settings'...
    xcopy /y /q "user_data\settings\*.txt" "%DIST_USER_DATA%\settings\"
) else (
    echo [WARN] No default settings found to copy. The 'settings' folder is empty.
)

:: (3) Remove sensitive files (Clean Up)
if exist "%DIST_USER_DATA%\settings\setup_gemini.txt" (
    del "%DIST_USER_DATA%\settings\setup_gemini.txt"
    echo [SECURE] Removed 'setup_gemini.txt' for privacy.
)

if exist "%DIST_USER_DATA%\neighbor_history.db" (
    del "%DIST_USER_DATA%\neighbor_history.db"
    echo [SECURE] Removed 'neighbor_history.db' for privacy.
)

:: Clear naver_profile directory (folder remains, files removed)
del /q "%DIST_USER_DATA%\naver_profile\*" 2>nul
echo [SECURE] Cleared 'naver_profile' directory.

:: 7. Copy extra files
echo [INFO] Copying README...
if exist "README.md" copy "README.md" "dist\" >nul

:: 8. Finish
echo ================================================
echo    [SUCCESS] Build completed successfully!
echo    output: dist\NaverBlogBot.exe
echo    UserData: dist\user_data (Clean)
echo ================================================

:: Open the output folder
start dist

pause
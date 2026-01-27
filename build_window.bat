@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo    Naver Blog Bot Build Process (Windows)
echo ================================================

if not exist "system\venv" (
    echo [WARN] Environment not found. Checking setup_venv.bat...
    if exist "setup_venv.bat" (
        call setup_venv.bat
    ) else (
        echo [ERROR] setup_venv.bat not found. Please set up venv first.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Environment venv detected. Skipping setup.
)

if exist "system\venv\Scripts\activate.bat" (
    echo [INFO] Activating system environment...
    call system\venv\Scripts\activate.bat
) else (
    echo [ERROR] Critical Error: Cannot find activate.bat!
    pause
    exit /b 1
)

echo [INFO] Checking build tools...
python -m pip install --upgrade pip >nul 2>&1
pip install pyinstaller >nul 2>&1

echo [INFO] Cleaning up previous build...
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist NaverBlogBot.spec del NaverBlogBot.spec

echo [INFO] Starting PyInstaller build process...
python -m PyInstaller --noconfirm --onedir --windowed --clean ^
    --name "NaverBlogBot" ^
    --add-data "system/bot_class;bot_class" ^
    "system/gui_main.py"

echo [INFO] Moving files to dist root...
xcopy /e /y /q "dist\NaverBlogBot\*" "dist\"
rd /s /q "dist\NaverBlogBot"

echo [INFO] Organizing user_data folder...
set "DIST_USER_DATA=dist\user_data"
if not exist "%DIST_USER_DATA%\settings" mkdir "%DIST_USER_DATA%\settings"
if not exist "%DIST_USER_DATA%\naver_profile" mkdir "%DIST_USER_DATA%\naver_profile"

if exist "system\settings" (
    xcopy /y /q "system\settings\*.txt" "%DIST_USER_DATA%\settings\"
    echo [INFO] Copied settings from system\settings.
) else if exist "user_data\settings" (
    xcopy /y /q "user_data\settings\*.txt" "%DIST_USER_DATA%\settings\"
    echo [INFO] Copied settings from user_data\settings.
)

if exist "%DIST_USER_DATA%\settings\setup_gemini.txt" (
    del /f /q "%DIST_USER_DATA%\settings\setup_gemini.txt"
    echo [SECURE] Removed setup_gemini.txt
)

if exist "%DIST_USER_DATA%\neighbor_history.db" (
    del /f /q "%DIST_USER_DATA%\neighbor_history.db"
    echo [SECURE] Removed neighbor_history.db
)

del /q "%DIST_USER_DATA%\naver_profile\*" 2>nul
echo [SECURE] Cleared naver_profile directory.

if exist "README.md" copy "README.md" "dist\" >nul

if %errorlevel% equ 0 (
    echo ================================================
    echo    ✅ Build completed successfully!
    echo    📂 Output: dist\NaverBlogBot.exe
    echo    📂 UserData: dist\user_data (Clean)
    echo ================================================
    start dist
) else (
    echo [ERROR] Build failed.
)

pause
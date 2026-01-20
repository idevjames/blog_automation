@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================================
echo     NAVER BLOG AUTOMATION BUILD START
echo ========================================================

:: 1. ����ȯ�� üũ �� Ȱ��ȭ (��θ� ������ ��� �����ϰ� ó��)
set "VENV_PATH=%~dp0system\venv\Scripts\activate.bat"

if exist "%VENV_PATH%" (
    echo Activating virtual environment...
    call "%VENV_PATH%"
) else (
    echo [ERROR] Virtual environment not found at: "%VENV_PATH%"
    pause
    exit /b 1
)

:: 2. ���Ӽ� ��ġ
echo Checking dependencies...
python -m pip install --upgrade pip
pip install PyQt6 selenium pyinstaller google-generativeai

:: 3. ���� ���� ����
echo Cleaning old files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

:: 4. PyInstaller ���� (�ٹٲ� ��ȣ ^ �ڿ� ���� ���� ����)
echo Running PyInstaller...
python -m PyInstaller --noconfirm --onedir --windowed --clean ^
 --add-data "system\settings;settings" ^
 --add-data "system\bot_class;bot_class" ^
 --collect-submodules "bot_class" ^
 "system\gui_main.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [BUILD FAILED] Check the errors above.
    pause
    exit /b 1
)

:: 5. ������ ���� ���� ����
echo Finalizing...
if not exist "dist\gui_main\settings" mkdir "dist\gui_main\settings"
copy "system\settings\*.txt" "dist\gui_main\settings\" >nul

echo.
echo ========================================================
echo     SUCCESSFULLY COMPLETED!
echo ========================================================
start explorer dist
pause
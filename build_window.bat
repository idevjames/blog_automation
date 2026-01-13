@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================================
echo     NAVER BLOG AUTOMATION BUILD START
echo ========================================================

:: 1. 가상환경 체크 및 활성화 (경로를 변수에 담아 안전하게 처리)
set "VENV_PATH=%~dp0system\venv\Scripts\activate.bat"

if exist "%VENV_PATH%" (
    echo Activating virtual environment...
    call "%VENV_PATH%"
) else (
    echo [ERROR] Virtual environment not found at: "%VENV_PATH%"
    pause
    exit /b 1
)

:: 2. 종속성 설치
echo Checking dependencies...
python -m pip install --upgrade pip
pip install PyQt6 selenium pyinstaller

:: 3. 빌드 잔재 삭제
echo Cleaning old files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

:: 4. PyInstaller 실행 (줄바꿈 기호 ^ 뒤에 공백 절대 금지)
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

:: 5. 배포용 설정 폴더 복사
echo Finalizing...
if not exist "dist\gui_main\settings" mkdir "dist\gui_main\settings"
copy "system\settings\*.txt" "dist\gui_main\settings\" >nul

echo.
echo ========================================================
echo     SUCCESSFULLY COMPLETED!
echo ========================================================
start explorer dist
pause
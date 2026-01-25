@echo off
setlocal enabledelayedexpansion

echo ================================================
echo    🚀 Naver Blog Bot Build Process (Windows)
echo ================================================

:: 1. 환경 설정 체크 (setup_venv.bat 연동)
if not exist "system\venv" (
    echo [WARN] Environment missing. Running setup_venv.bat...
    call setup_venv.bat
) else (
    echo [INFO] Environment (system\venv) detected. Skipping setup.
)

:: 2. 가상환경 활성화
if exist "system\venv\Scripts\activate.bat" (
    echo [INFO] Activating system\venv environment...
    call system\venv\Scripts\activate.bat
) else (
    echo [ERROR] Critical Error: Cannot find system\venv\Scripts\activate.bat
    pause
    exit /b 1
)

:: 3. 이전 빌드 캐시 정리
echo [INFO] Cleaning up previous build (build, dist, spec)...
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist gui_main.spec del /q gui_main.spec

:: 4. PyInstaller 빌드 실행
echo [INFO] Starting PyInstaller build process...
python -m PyInstaller --noconfirm --onedir --windowed --clean ^
    --add-data "system/bot_class;bot_class" ^
    "system/gui_main.py"

:: 5. [핵심] 사용자 데이터 폴더(user_data) 구성
echo [INFO] Organizing 'user_data' folder for distribution...
if not exist "dist\user_data\settings" mkdir "dist\user_data\settings"
if not exist "dist\user_data\naver_profile" mkdir "dist\user_data\naver_profile"

:: 초기 설정 파일 복사
if exist "system\settings" (
    xcopy "system\settings\*.txt" "dist\user_data\settings\" /Y /E
    echo [OK] Default settings copied to user_data\settings.
)

:: 6. 추가 파일 복사
if exist "README.md" copy "README.md" "dist\"
if exist "setup_venv.bat" copy "setup_venv.bat" "dist\"

:: 7. 결과 확인
if %errorlevel% equ 0 (
    echo ================================================
    echo    ✅ Build completed successfully!
    echo    📂 Simply copy 'user_data' to keep settings.
    echo ================================================
    start dist
) else (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

pause
@echo off
:: 한글 출력을 위해 코드페이지 변경 (필요 시)
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo    🚀 네이버 블로그 자동화 봇 빌드 시작 (Windows)
echo ========================================================
echo.

:: 1. 가상환경 활성화 체크
if exist "system\venv\Scripts\activate.bat" (
    echo 📦 system\venv 가상환경을 활성화합니다...
    call system\venv\Scripts\activate.bat
) else (
    echo ⚠️  가상환경(system\venv)을 찾을 수 없습니다!
    echo 현재 경로: %cd%
    pause
    exit /b 1
)

:: 2. 필수 라이브러리 및 빌드 도구 설치/업데이트
echo 🛠️  빌드에 필요한 라이브러리 점검 중...
pip install --upgrade pip
pip install PyQt6 selenium pyinstaller

:: 3. 이전 빌드 파일 및 캐시 청소
echo 🧹 기존 빌드 폴더(build, dist) 및 spec 파일을 정리합니다...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "gui_main.spec" del /q "gui_main.spec"

:: 4. PyInstaller 빌드 실행
:: [주의] Windows에서는 --add-data 구분자가 세미콜론(;)입니다.
echo 🏗️  PyInstaller를 사용하여 실행 파일 빌드를 시작합니다...

python -m PyInstaller --noconfirm --onedir --windowed --clean ^
    --add-data "system\settings;settings" ^
    --add-data "system\bot_class;bot_class" ^
    --collect-submodules "bot_class" ^
    "system\gui_main.py"

if %errorlevel% neq 0 (
    echo ❌ 빌드 과정 중 오류가 발생했습니다.
    pause
    exit /b 1
)

:: 5. [핵심] 실제 사용자가 수정할 외부 설정 폴더 구성
echo 🚚 사용자용 외부 설정 파일 폴더를 구성합니다...
if not exist "dist\settings" mkdir "dist\settings"
copy "system\settings\*.txt" "dist\settings\" >nul

:: 6. 추가 배포 파일 복사 (README, 실행 스크립트 등)
echo 📝 추가 배포 파일(README, run.bat) 복사 중...
if exist "README.md" copy "README.md" "dist\" >nul
:: 윈도우이므로 run.command 대신 run.bat를 복사합니다.
if exist "run.bat" copy "run.bat" "dist\" >nul

:: 7. 결과 확인 및 폴더 열기
echo.
echo ========================================================
echo    ✅ 모든 빌드 과정이 성공적으로 완료되었습니다!
echo    📂 dist 폴더 내 패키지를 압축하여 배포하세요.
echo ========================================================
echo.

start explorer dist
pause
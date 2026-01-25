#!/bin/bash

# 색상 정의 (Terminal Output Colors)
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   🚀 Naver Blog Bot Build Process (macOS)      ${NC}"
echo -e "${BLUE}================================================${NC}"

# 1. 환경 설정 체크 (setup_venv.command 연동)
if [ ! -d "system/venv" ]; then
    echo -e "${BLUE}[WARN] Environment not found. Running setup_venv.command...${NC}"
    chmod +x setup_venv.command
    ./setup_venv.command
else
    echo -e "${GREEN}[INFO] Environment (system/venv) detected. Skipping setup.${NC}"
fi

# 2. 가상환경 활성화
if [ -f "system/venv/bin/activate" ]; then
    echo -e "📦 Activating system/venv environment..."
    source system/venv/bin/activate
else
    echo -e "${RED}⚠️  Critical Error: Cannot find system/venv/bin/activate!${NC}"
    exit 1
fi

# 3. 빌드 도구 점검
echo -e "${BLUE}🛠️  Checking build tools...${NC}"
pip install --upgrade pip > /dev/null
pip install pyinstaller > /dev/null

# 4. 이전 빌드 캐시 정리
echo -e "🧹 Cleaning up previous build (build, dist, spec)..."
rm -rf build dist gui_main.spec

# 5. PyInstaller 빌드 실행
# 소스 코드는 system 내부에 있지만, 실행 시 외부 user_data를 바라봅니다.
echo -e "${BLUE}🏗️  Starting PyInstaller build process...${NC}"

python3 -m PyInstaller --noconfirm --onedir --windowed --clean \
    --add-data "system/bot_class:bot_class" \
    --add-data "system/ai_helper.py:." \
    "system/gui_main.py"

# 6. [핵심] 사용자 데이터 폴더(user_data) 구성
# 배포판 루트에 user_data 폴더를 만들고 초기 설정 파일들을 복사합니다.
echo -e "🚚 Organizing 'user_data' folder for distribution..."
mkdir -p dist/user_data/settings
mkdir -p dist/user_data/naver_profile

# 초기 설정 .txt 파일 복사 (setup_gemini.txt 포함 여부는 선택)
if [ -d "system/settings" ]; then
    cp system/settings/*.txt dist/user_data/settings/
    echo -e "${GREEN}✅ Default settings copied to user_data/settings.${NC}"
fi

# 7. 추가 배포 파일 복사
echo -e "📝 Copying README and setup scripts..."
[ -f "README.md" ] && cp "README.md" dist/
[ -f "setup_venv.command" ] && cp "setup_venv.command" dist/

# 8. 결과 확인
if [ $? -eq 0 ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}   ✅ Build completed successfully!             ${NC}"
    echo -e "${GREEN}   📂 Copy the 'user_data' folder to update.    ${NC}"
    echo -e "================================================${NC}"
    open dist/
else
    echo -e "${RED}❌ Error occurred during the build process.${NC}"
    exit 1
fi
#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   🚀 Naver Blog Bot Build Process (macOS)      ${NC}"
echo -e "${BLUE}================================================${NC}"

# 1. 환경 설정 체크
if [ ! -d "system/venv" ]; then
    echo -e "${YELLOW}[WARN] Environment not found. Checking setup_venv...${NC}"
    if [ -f "setup_venv.command" ]; then
        chmod +x setup_venv.command
        ./setup_venv.command
    else
        echo -e "${RED}❌ setup_venv.command not found. Please set up venv first.${NC}"
        exit 1
    fi
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
echo -e "${BLUE}🏗️  Starting PyInstaller build process...${NC}"

# [수정됨] --add-data "system/settings:settings" 라인을 제거했습니다.
# 이유: 이제 설정은 앱 내부가 아닌 외부(user_data)에서 불러옵니다.
python3 -m PyInstaller --noconfirm --onedir --windowed --clean \
    --name "NaverBlogBot" \
    --add-data "system/bot_class:bot_class" \
    "system/gui_main.py"

# 6. 배포용 user_data 폴더 구성
echo -e "${BLUE}🚚 Organizing 'user_data' folder for distribution...${NC}"

DIST_USER_DATA="dist/user_data"

# (1) 폴더 뼈대 생성
mkdir -p "$DIST_USER_DATA/settings"
mkdir -p "$DIST_USER_DATA/naver_profile"

# (2) 기본 설정 파일 복사
# [수정됨] system/settings가 없으면 현재 작업 중인 user_data/settings에서 복사해옵니다.
if [ -d "system/settings" ]; then
    cp system/settings/*.txt "$DIST_USER_DATA/settings/"
    echo -e "${GREEN}   ✅ Copied default settings from 'system/settings'.${NC}"
elif [ -d "user_data/settings" ]; then
    cp user_data/settings/*.txt "$DIST_USER_DATA/settings/"
    echo -e "${GREEN}   ✅ Copied default settings from 'user_data/settings'.${NC}"
else
    echo -e "${RED}⚠️  Warning: No default settings found to copy. The 'settings' folder is empty.${NC}"
fi

# (3) 민감 정보 파일 삭제 (Clean Up)
if [ -f "$DIST_USER_DATA/settings/setup_gemini.txt" ]; then
    rm "$DIST_USER_DATA/settings/setup_gemini.txt"
    echo -e "${YELLOW}   🔒 Removed 'setup_gemini.txt' for privacy.${NC}"
fi

if [ -f "$DIST_USER_DATA/neighbor_history.db" ]; then
    rm "$DIST_USER_DATA/neighbor_history.db"
    echo -e "${YELLOW}   🔒 Removed 'neighbor_history.db' for privacy.${NC}"
fi

rm -rf "$DIST_USER_DATA/naver_profile/*"
echo -e "${YELLOW}   🔒 Cleared 'naver_profile' directory.${NC}"

# 7. 추가 배포 파일 복사
echo -e "📝 Copying README..."
[ -f "README.md" ] && cp "README.md" dist/

# 8. 결과 확인
if [ $? -eq 0 ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}   ✅ Build completed successfully!             ${NC}"
    echo -e "${GREEN}   📂 Output: dist/NaverBlogBot.app             ${NC}"
    echo -e "${GREEN}   📂 UserData: dist/user_data (Clean)          ${NC}"
    echo -e "${BLUE}================================================${NC}"
    
    open dist/
else
    echo -e "${RED}❌ Error occurred during the build process.${NC}"
    exit 1
fi
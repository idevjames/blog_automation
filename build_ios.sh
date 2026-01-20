#!/bin/bash

# 색상 정의 (터미널 출력 가독성용)
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   🚀 네이버 블로그 자동화 봇 빌드 시작 (macOS)   ${NC}"
echo -e "${BLUE}================================================${NC}"

# 1. 가상환경 활성화 체크
if [ -f "system/venv/bin/activate" ]; then
    echo -e "📦 system/venv 가상환경을 활성화합니다..."
    source system/venv/bin/activate
else
    echo -e "${RED}⚠️  가상환경(system/venv)을 찾을 수 없습니다!${NC}"
    echo -e "현재 경로: $(pwd)"
    exit 1
fi

# 2. 필수 라이브러리 및 빌드 도구 설치/업데이트
echo -e "${BLUE}🛠️  빌드에 필요한 라이브러리 점검 중...${NC}"
pip install --upgrade pip
pip install PyQt6 selenium pyinstaller google-generativeai

# 3. 이전 빌드 파일 및 캐시 청소
echo -e "🧹 기존 빌드 폴더(build, dist) 및 spec 파일을 정리합니다..."
rm -rf build dist gui_main.spec

# 4. PyInstaller 빌드 실행
# --add-data "소스:목적지" 형식으로 내부 리소스 포함
echo -e "${BLUE}🏗️  PyInstaller를 사용하여 실행 파일 빌드를 시작합니다...${NC}"

python3 -m PyInstaller --noconfirm --onedir --windowed --clean \
    --add-data "system/bot_class:bot_class" \
    --add-data "system/ai_helper.py:." \
    --collect-submodules "bot_class" \
    "system/gui_main.py"

# 5. [핵심] 실제 사용자가 수정할 외부 설정 폴더 구성
# 빌드된 앱 내부의 settings는 초기값이 되고, 
# 앱 옆에 복사된 이 settings 폴더의 파일들이 실제 저장/수정 대상이 됩니다.
echo -e "🚚 사용자용 외부 설정 파일 폴더를 구성합니다..."
mkdir -p dist/settings
rsync -av --exclude='setup_gemini.txt' system/settings/*.txt dist/settings/

echo -e "${GREEN}✅ setup_gemini.txt를 제외한 설정 파일 복사 완료!${NC}"

# 6. 추가 배포 파일 복사 (README, 실행 스크립트 등)
echo -e "📝 추가 배포 파일(README, command) 복사 중..."
[ -f "README.md" ] && cp "README.md" dist/
[ -f "run.command" ] && cp "run.command" dist/

# 7. 결과 확인
if [ $? -eq 0 ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}   ✅ 모든 빌드 과정이 성공적으로 완료되었습니다!   ${NC}"
    echo -e "${GREEN}   📂 dist 폴더 내 패키지를 압축하여 배포하세요.      ${NC}"
    echo -e "${GREEN}================================================${NC}"
    # 결과 폴더 열기
    open dist/
else
    echo -e "${RED}❌ 빌드 과정 중 오류가 발생했습니다.${NC}"
    exit 1
fi
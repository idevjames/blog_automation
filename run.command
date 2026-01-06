#!/bin/bash

# 1. 현재 폴더(루트)로 이동
cd "$(dirname "$0")" || exit

echo "============================================="
echo " 🤖 네이버 블로그 봇 실행기"
echo "============================================="
echo

# 2. 시스템 폴더 확인
if [ ! -d "system" ]; then
    echo "❌ 오류: 'system' 폴더가 없습니다."
    echo "   소스코드들을 'system' 폴더 안에 넣어주세요."
    read -p "엔터를 누르면 종료합니다..."
    exit 1
fi

# 3. 가상환경 확인 및 생성
if [ ! -d "system/venv" ]; then
    echo "📦 가상환경 폴더가 없어서 새로 만듭니다..."
    python3 -m venv system/venv
fi

# 4. 가상환경 활성화
source system/venv/bin/activate

# 5. 필수 라이브러리 설치/업데이트
# (pip 대신 python3 -m pip 사용 -> 오류 해결 포인트)
echo "📦 라이브러리를 확인하고 설치합니다..."
python3 -m pip install --upgrade pip
python3 -m pip install selenium webdriver-manager requests

echo "✅ 준비 완료."
echo

# 6. 프로그램 실행
# PYTHONPATH를 현재 폴더(루트)로 잡아줘서 system 내부에서 상위 폴더 파일을 인식하게 함
export PYTHONPATH=$PYTHONPATH:$(pwd)

if [ -f "system/main.py" ]; then
    echo "🚀 봇을 실행합니다..."
    echo "---------------------------------------------"
    python3 system/main.py
else
    echo "❌ 오류: system/main.py 파일을 찾을 수 없습니다."
fi

echo
echo "============================================="
echo "프로그램이 종료되었습니다."
read -p "창을 닫으려면 아무 키나 누르세요..."
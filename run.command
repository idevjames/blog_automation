#!/bin/bash

# 1. 현재 폴더(루트)로 이동
cd "$(dirname "$0")" || exit

echo "============================================="
echo " 🤖 네이버 블로그 봇 실행기 (macOS 3.11)"
echo "============================================="
echo

# 2. 시스템 폴더 확인
if [ ! -d "system" ]; then
    echo "❌ 오류: 'system' 폴더가 없습니다."
    echo "   소스코드들을 'system' 폴더 안에 넣어주세요."
    read -p "엔터를 누르면 종료합니다..."
    exit 1
fi

# 3. 가상환경 확인 및 자동 설치 (Python 3.11 기반)
if [ ! -d "system/venv" ]; then
    echo "📦 초기 설정: Python 3.11 가상환경을 설치합니다..."
    # PATH에 등록된 python3.11을 명시적으로 사용하여 가상환경 생성
    python3.11 -m venv system/venv
    
    if [ $? -ne 0 ]; then
        echo "❌ 오류: Python 3.11 설치가 확인되지 않습니다."
        echo "   brew install python@3.11 을 먼저 완료해주세요."
        read -p "엔터를 누르면 종료합니다..."
        exit 1
    fi
    
    source system/venv/bin/activate
    pip install --upgrade pip
    # PyQt6 라이브러리 추가 설치
    pip install selenium requests PyQt6 google-generativeai
    echo "✅ 설치 완료."
else
    source system/venv/bin/activate
fi

# 4. 프로그램 실행 (PYTHONPATH 설정으로 모듈 경로 인식 해결)
export PYTHONPATH=$PYTHONPATH:$(pwd)

# GUI 메인 파일이 있는지 먼저 확인하고 실행
if [ -f "system/gui_main.py" ]; then
    echo "🚀 GUI 봇을 실행합니다..."
    echo "---------------------------------------------"
    python system/gui_main.py
elif [ -f "system/gui_main.py" ]; then
    echo "🚀 터미널 봇을 실행합니다..."
    echo "---------------------------------------------"
    python system/gui_main.py
else
    echo "❌ 오류: 실행할 파이썬 파일(gui_main.py)을 찾을 수 없습니다."
fi

echo
echo "============================================="
echo "프로그램이 종료되었습니다."
read -p "창을 닫으려면 아무 키나 누르세요..."
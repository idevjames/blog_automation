#!/bin/bash
cd "$(dirname "$0")"

echo "============================================="
echo "  🍎 Environment Setup Check (macOS)"
echo "============================================="

# 1. 가상환경 폴더 확인 및 생성
if [ -d "system/venv" ]; then
    echo "[INFO] 가상환경이 이미 존재합니다."
else
    echo "[INFO] 가상환경이 없습니다. 새로 생성 중..."
    python3 -m venv system/venv
fi

# 2. 가상환경 내 경로 지정 (Mac은 Scripts 대신 bin을 사용합니다)
PYTHON_PATH="./system/venv/bin/python3"
PIP_PATH="./system/venv/bin/pip3"

echo "[INFO] pip 업그레이드 중..."
$PYTHON_PATH -m pip install --upgrade pip

echo "[INFO] 라이브러리 설치 중 (google-genai 버전)..."
$PIP_PATH install selenium requests PyQt6 pyinstaller google-genai webdriver-manager

echo "============================================="
echo "[OK] 설치 완료! 이제 프로그램을 실행할 수 있습니다."
echo "============================================="
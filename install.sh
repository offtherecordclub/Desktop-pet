#!/bin/bash
# AI 데스크탑 펫 설치 스크립트
# Mac용

echo "🐾 AI Desktop Pet 설치 중..."

# Python3 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3가 필요해요. https://www.python.org 에서 설치해주세요."
    exit 1
fi

echo "✅ Python3 발견: $(python3 --version)"

# pip로 pygame 설치
echo "📦 pygame 설치 중..."
pip3 install pygame --quiet

# (선택) pyobjc - always-on-top 기능
echo "📦 pyobjc 설치 시도 중... (실패해도 OK)"
pip3 install pyobjc-framework-Cocoa --quiet 2>/dev/null && echo "✅ pyobjc OK" || echo "⚠️  pyobjc 없어도 동작함"

echo ""
echo "✅ 설치 완료!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 실행 방법:"
echo "   python3 pet.py"
echo ""
echo "🎮 조작법:"
echo "   ■ 왼쪽 버튼  = 전원 ON/OFF"
echo "   ▶ 가운데 버튼 = 다음 메시지"
echo "   ● 오른쪽 버튼 = 메시지 멈추기 & 춤추기"
echo "   드래그        = 창 이동"
echo "   ESC           = 종료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

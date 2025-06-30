#!/usr/bin/env python3
"""
Gemini API 간단 테스트 스크립트 (텍스트 생성만)
"""

import os
import sys
import time
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ python-dotenv가 설치되지 않았습니다.")
    sys.exit(1)

# 환경 변수 로드
env_file = project_root / ".env.local"
if env_file.exists():
    load_dotenv(env_file)

try:
    from src.api.gemini_api import GeminiAPI
    from src.config import settings
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    sys.exit(1)


def test_gemini_text():
    """Gemini 텍스트 생성 간단 테스트"""
    print("🧠 Gemini 텍스트 생성 테스트")
    print("=" * 40)
    
    gemini_api = GeminiAPI()
    
    test_messages = [
        [{"role": "user", "content": "안녕하세요! 간단한 인사말을 해주세요."}],
        [{"role": "user", "content": "파이썬의 장점 3가지를 알려주세요."}]
    ]
    
    for i, messages in enumerate(test_messages, 1):
        try:
            print(f"\n📝 테스트 {i}: {messages[0]['content'][:30]}...")
            
            start_time = time.time()
            response = gemini_api.generate_text(
                messages=messages,
                temperature=0.7
            )
            end_time = time.time()
            
            content = gemini_api.extract_text_from_response(response)
            
            print(f"✅ 성공 - {round(end_time - start_time, 2)}초")
            print(f"📄 응답: {content[:200]}...")
            
        except Exception as e:
            print(f"❌ 실패: {e}")
    
    print("\n✅ Gemini 텍스트 테스트 완료!")


if __name__ == "__main__":
    test_gemini_text()
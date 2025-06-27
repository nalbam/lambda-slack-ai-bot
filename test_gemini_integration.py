#!/usr/bin/env python3
"""
Gemini API 통합 테스트 스크립트
"""
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 테스트용 환경 변수 설정 (실제 값이 없으면 더미 값 사용)
os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test")
os.environ.setdefault("SLACK_SIGNING_SECRET", "test-secret")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("OPENAI_ORG_ID", "org-test")

try:
    from src.api.gemini_api import gemini_api, GeminiApiError
    print("✅ Gemini API 모듈 임포트 성공")
except ImportError as e:
    print(f"❌ Gemini API 모듈 임포트 실패: {e}")
    print("google-genai 패키지를 설치해주세요: pip install google-genai")
    sys.exit(1)

def test_gemini_text_generation():
    """Gemini 텍스트 생성 테스트"""
    print("\n🧪 Gemini 텍스트 생성 테스트...")
    
    try:
        messages = [
            {"role": "user", "content": "안녕하세요! 간단한 인사말로 답변해주세요."}
        ]
        
        response = gemini_api.generate_text(messages, stream=False)
        text = gemini_api.extract_text_from_response(response)
        
        print(f"✅ 텍스트 생성 성공: {text[:100]}...")
        return True
        
    except GeminiApiError as e:
        print(f"❌ Gemini API 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

def test_gemini_image_analysis():
    """Gemini 이미지 분석 테스트 (더미 데이터)"""
    print("\n🧪 Gemini 이미지 분석 테스트...")
    
    try:
        # 1x1 픽셀 PNG 이미지 (Base64)
        dummy_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA2lMpNwAAAABJRU5ErkJggg=="
        
        response = gemini_api.analyze_image(
            image_data=dummy_image,
            prompt="이 이미지를 설명해주세요.",
            mime_type="image/png"
        )
        
        text = gemini_api.extract_text_from_response(response)
        print(f"✅ 이미지 분석 성공: {text[:100]}...")
        return True
        
    except GeminiApiError as e:
        print(f"❌ Gemini API 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

def test_unsupported_features():
    """지원되지 않는 기능 테스트"""
    print("\n🧪 지원되지 않는 기능 테스트...")
    
    # 이미지 생성 테스트
    try:
        gemini_api.generate_image("test prompt")
        print("❌ 이미지 생성이 예상과 다르게 성공함")
        return False
    except GeminiApiError as e:
        print(f"✅ 이미지 생성 미지원 확인: {e}")
    
    # 비디오 생성 테스트  
    try:
        gemini_api.generate_video("test prompt")
        print("❌ 비디오 생성이 예상과 다르게 성공함")
        return False
    except GeminiApiError as e:
        print(f"✅ 비디오 생성 미지원 확인: {e}")
    
    return True

def main():
    """메인 테스트 함수"""
    print("🚀 Gemini API 통합 테스트 시작")
    
    # 환경 변수 확인
    if not os.getenv('GEMINI_API_KEY') and not os.getenv('GOOGLE_API_KEY'):
        print("⚠️  GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("실제 API 테스트는 건너뛰고 모듈 로딩만 확인합니다.")
        print("✅ 모듈 통합 테스트 완료")
        return
    
    # 실제 API 테스트
    success_count = 0
    total_tests = 3
    
    if test_gemini_text_generation():
        success_count += 1
    
    if test_gemini_image_analysis():
        success_count += 1
        
    if test_unsupported_features():
        success_count += 1
    
    print(f"\n📊 테스트 결과: {success_count}/{total_tests} 성공")
    
    if success_count == total_tests:
        print("🎉 모든 테스트 통과!")
    else:
        print("⚠️  일부 테스트 실패")

if __name__ == "__main__":
    main()
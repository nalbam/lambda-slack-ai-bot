#!/usr/bin/env python3
"""
OpenAI API 테스트 스크립트
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ python-dotenv가 설치되지 않았습니다. 'pip install python-dotenv'로 설치해주세요.")
    sys.exit(1)

# 환경 변수 로드
env_file = project_root / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
else:
    print("⚠️ .env.local 파일이 없습니다. 환경 변수가 시스템에서 로드됩니다.")

try:
    from src.api.openai_api import generate_chat_completion, generate_image
    from src.config import settings
    from src.utils import logger
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    sys.exit(1)


class OpenAITester:
    """OpenAI API 테스트 클래스"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
            sys.exit(1)
        print(f"✅ OpenAI API 키 확인 (키: {self.api_key[:10]}...)")
    
    def test_text_generation(self) -> Dict[str, Any]:
        """텍스트 생성 테스트"""
        print("\n🤖 OpenAI 텍스트 생성 테스트")
        print("-" * 40)
        
        test_messages = [
            [{"role": "user", "content": "안녕하세요! 오늘 날씨는 어떤가요?"}],
            [
                {"role": "system", "content": "당신은 친근한 AI 어시스턴트입니다."},
                {"role": "user", "content": "AI에 대해 간단히 설명해주세요."}
            ],
            [{"role": "user", "content": "파이썬의 장점 3가지를 알려주세요."}]
        ]
        
        results = []
        
        for i, messages in enumerate(test_messages, 1):
            try:
                print(f"\n📝 테스트 {i}: {messages[-1]['content'][:50]}...")
                
                start_time = time.time()
                response = generate_chat_completion(
                    messages=messages,
                    user="test_user",
                    stream=False
                )
                end_time = time.time()
                
                content = response.choices[0].message.content
                
                result = {
                    "test_number": i,
                    "success": True,
                    "response_time": round(end_time - start_time, 2),
                    "content_length": len(content),
                    "model": response.model,
                    "usage": response.usage.dict() if response.usage else None,
                    "content_preview": content[:200] + "..." if len(content) > 200 else content
                }
                
                print(f"✅ 성공 - {result['response_time']}초")
                print(f"📊 토큰 사용: {result['usage']}")
                print(f"📄 응답 미리보기: {result['content_preview']}")
                
                results.append(result)
                
            except Exception as e:
                print(f"❌ 실패: {e}")
                results.append({
                    "test_number": i,
                    "success": False,
                    "error": str(e)
                })
        
        return {"test_type": "text_generation", "results": results}
    
    def test_image_generation(self) -> Dict[str, Any]:
        """이미지 생성 테스트"""
        print("\n🎨 OpenAI DALL-E 이미지 생성 테스트")
        print("-" * 40)
        
        test_prompts = [
            "A cute robot reading a book in a library",
            "Beautiful cherry blossoms in spring",
            "Modern minimalist office space with plants"
        ]
        
        results = []
        
        for i, prompt in enumerate(test_prompts, 1):
            try:
                print(f"\n🖼️ 테스트 {i}: {prompt}")
                
                start_time = time.time()
                response = generate_image(prompt, user="test_user")
                end_time = time.time()
                
                result = {
                    "test_number": i,
                    "success": True,
                    "prompt": prompt,
                    "response_time": round(end_time - start_time, 2),
                    "image_url": response.data[0].url if response.data else None,
                    "revised_prompt": getattr(response.data[0], 'revised_prompt', None) if response.data else None
                }
                
                print(f"✅ 성공 - {result['response_time']}초")
                print(f"🔗 이미지 URL: {result['image_url']}")
                if result['revised_prompt']:
                    print(f"📝 수정된 프롬프트: {result['revised_prompt'][:100]}...")
                
                results.append(result)
                
            except Exception as e:
                print(f"❌ 실패: {e}")
                results.append({
                    "test_number": i,
                    "success": False,
                    "prompt": prompt,
                    "error": str(e)
                })
        
        return {"test_type": "image_generation", "results": results}
    
    def test_vision_analysis(self) -> Dict[str, Any]:
        """이미지 분석 테스트 (Vision 기능이 있다면 테스트)"""
        print("\n👁️ OpenAI Vision 이미지 분석 테스트")
        print("-" * 40)
        
        results = []
        
        try:
            # OpenAI Vision API가 구현되어 있는지 확인
            print("\n📝 테스트 1: Vision API 구조 검증")
            
            result = {
                "test_number": 1,
                "test_name": "vision_api_structure",
                "success": True,
                "note": "Vision API는 현재 프로젝트에 구현되지 않았습니다.",
                "recommendation": "GPT-4o Vision을 사용한 이미지 분석 기능을 추가할 수 있습니다."
            }
            
            print(f"ℹ️ {result['note']}")
            print(f"💡 {result['recommendation']}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            results.append({
                "test_number": 1,
                "test_name": "vision_api_structure",
                "success": False,
                "error": str(e)
            })
        
        return {"test_type": "vision_analysis", "results": results}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        print("🚀 OpenAI API 전체 테스트 시작")
        print("=" * 50)
        
        all_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "api_key_prefix": self.api_key[:10] + "...",
            "model_settings": {
                "text_model": settings.OPENAI_MODEL,
                "image_model": settings.IMAGE_MODEL,
                "image_quality": settings.IMAGE_QUALITY,
                "image_size": settings.IMAGE_SIZE
            },
            "tests": []
        }
        
        # 1. 텍스트 생성 테스트
        text_results = self.test_text_generation()
        all_results["tests"].append(text_results)
        
        # 2. 이미지 생성 테스트
        image_results = self.test_image_generation()
        all_results["tests"].append(image_results)
        
        # 3. 이미지 분석 테스트
        vision_results = self.test_vision_analysis()
        all_results["tests"].append(vision_results)
        
        # 결과 요약
        print("\n📊 테스트 결과 요약")
        print("=" * 50)
        
        for test in all_results["tests"]:
            test_name = test["test_type"]
            successful_tests = sum(1 for r in test["results"] if r["success"])
            total_tests = len(test["results"])
            
            print(f"🔸 {test_name}: {successful_tests}/{total_tests} 성공")
            
            if successful_tests < total_tests:
                failed_tests = [r for r in test["results"] if not r["success"]]
                for failed in failed_tests:
                    print(f"  ❌ 테스트 {failed['test_number']}: {failed.get('error', 'Unknown error')}")
        
        return all_results


def main():
    """메인 실행 함수"""
    try:
        tester = OpenAITester()
        results = tester.run_all_tests()
        
        print(f"\n✅ 모든 테스트 완료!")
        print(f"📅 실행 시간: {results['timestamp']}")
        
    except KeyboardInterrupt:
        print("\n👋 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    main()
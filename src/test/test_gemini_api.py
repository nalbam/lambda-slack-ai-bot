#!/usr/bin/env python3
"""
Gemini API 테스트 스크립트
"""

import os
import sys
import time
import base64
import requests
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
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ google-genai가 설치되지 않았습니다. 'pip install google-genai'로 설치해주세요.")
    sys.exit(1)

try:
    from src.api.gemini_api import GeminiAPI, GeminiApiError
    from src.config import settings
    from src.utils import logger
    import requests
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    sys.exit(1)


class GeminiTester:
    """Gemini API 테스트 클래스"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            print("❌ GEMINI_API_KEY 또는 GOOGLE_API_KEY가 설정되지 않았습니다.")
            sys.exit(1)
        
        # output 디렉토리 생성
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        self.gemini_api = GeminiAPI()
        self.client = genai.Client(api_key=self.api_key)
        print(f"✅ Gemini API 키 확인 (키: {self.api_key[:10]}...)")
        print(f"📁 파일 저장 경로: {self.output_dir}")
    
    def save_image_bytes(self, image_bytes: bytes, filename: str) -> str:
        """이미지 바이트 데이터를 파일로 저장합니다.
        
        Args:
            image_bytes: 이미지 바이트 데이터
            filename: 저장할 파일명
            
        Returns:
            저장된 파일의 전체 경로
        """
        try:
            file_path = self.output_dir / filename
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
            
            return str(file_path)
        except Exception as e:
            print(f"⚠️ 이미지 저장 실패: {e}")
            return ""
    
    def save_video_bytes(self, video_bytes: bytes, filename: str) -> str:
        """비디오 바이트 데이터를 파일로 저장합니다.
        
        Args:
            video_bytes: 비디오 바이트 데이터
            filename: 저장할 파일명
            
        Returns:
            저장된 파일의 전체 경로
        """
        try:
            file_path = self.output_dir / filename
            with open(file_path, 'wb') as f:
                f.write(video_bytes)
            
            return str(file_path)
        except Exception as e:
            print(f"⚠️ 비디오 저장 실패: {e}")
            return ""
    
    def download_and_save_file(self, file_url: str, filename: str) -> str:
        """URL에서 파일을 다운로드하고 저장합니다.
        
        Args:
            file_url: 다운로드할 파일 URL
            filename: 저장할 파일명
            
        Returns:
            저장된 파일의 전체 경로
        """
        try:
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            
            file_path = self.output_dir / filename
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return str(file_path)
        except Exception as e:
            print(f"⚠️ 파일 다운로드 실패: {e}")
            return ""
    
    def test_text_generation(self) -> Dict[str, Any]:
        """텍스트 생성 테스트"""
        print("\n🤖 Gemini 텍스트 생성 테스트")
        print("-" * 40)
        
        test_messages = [
            [{"role": "user", "content": "안녕하세요! 오늘은 좋은 하루인가요?"}],
            [
                {"role": "system", "content": "당신은 친근하고 도움이 되는 AI입니다."},
                {"role": "user", "content": "인공지능의 미래에 대해 어떻게 생각하시나요?"}
            ],
            [{"role": "user", "content": "파이썬과 자바스크립트의 차이점을 설명해주세요."}],
            [{"role": "user", "content": "한국의 전통 음식 5가지를 추천해주세요."}]
        ]
        
        results = []
        
        for i, messages in enumerate(test_messages, 1):
            try:
                print(f"\n📝 테스트 {i}: {messages[-1]['content'][:50]}...")
                
                start_time = time.time()
                response = self.gemini_api.generate_text(
                    messages=messages,
                    temperature=0.7,
                    stream=False
                )
                end_time = time.time()
                
                content = self.gemini_api.extract_text_from_response(response)
                
                result = {
                    "test_number": i,
                    "success": True,
                    "response_time": round(end_time - start_time, 2),
                    "content_length": len(content),
                    "model": settings.GEMINI_TEXT_MODEL,
                    "content_preview": content[:200] + "..." if len(content) > 200 else content
                }
                
                print(f"✅ 성공 - {result['response_time']}초")
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
        print("\n🎨 Gemini Imagen 이미지 생성 테스트")
        print("-" * 40)
        
        test_prompts = [
            "A futuristic robot in a beautiful garden",
            "Mountain landscape at sunset with cherry blossoms",
            "Modern minimalist kitchen with natural lighting"
        ]
        
        results = []
        
        for i, prompt in enumerate(test_prompts, 1):
            try:
                print(f"\n🖼️ 테스트 {i}: {prompt}")
                
                start_time = time.time()
                response = self.gemini_api.generate_image(
                    prompt=prompt,
                    aspect_ratio="1:1"
                )
                end_time = time.time()
                
                has_images = bool(response.get('images') or response.get('candidates') or response.get('generated_images'))
                saved_path = ""
                
                # 이미지가 생성된 경우 저장 시도
                if has_images:
                    try:
                        # 이미지 데이터 추출
                        image_bytes = None
                        
                        # 1. generated_images에서 추출 시도 (Gemini API v1beta 방식)
                        if response.get('generated_images'):
                            for img in response['generated_images']:
                                if hasattr(img, 'image') and hasattr(img.image, 'image_bytes'):
                                    image_bytes = img.image.image_bytes
                                    break
                                elif hasattr(img, 'image_bytes'):
                                    image_bytes = img.image_bytes
                                    break
                        
                        # 2. candidates에서 추출 시도 (차선책)
                        if not image_bytes and response.get('candidates'):
                            for candidate in response['candidates']:
                                if hasattr(candidate, 'image') and hasattr(candidate.image, 'image_bytes'):
                                    image_bytes = candidate.image.image_bytes
                                    break
                                elif hasattr(candidate, 'image_bytes'):
                                    image_bytes = candidate.image_bytes
                                    break
                        
                        # 3. images에서 추출 시도 (차선책)
                        if not image_bytes and response.get('images'):
                            for img in response['images']:
                                if hasattr(img, 'image') and hasattr(img.image, 'image_bytes'):
                                    image_bytes = img.image.image_bytes
                                    break
                                elif hasattr(img, 'image_bytes'):
                                    image_bytes = img.image_bytes
                                    break
                        
                        # 이미지 바이트가 있으면 저장
                        if image_bytes:
                            timestamp = time.strftime("%Y%m%d_%H%M%S")
                            filename = f"gemini_image_test_{i}_{timestamp}.png"
                            saved_path = self.save_image_bytes(image_bytes, filename)
                            
                    except Exception as save_error:
                        print(f"⚠️ 이미지 저장 중 오류: {save_error}")
                        saved_path = ""
                
                result = {
                    "test_number": i,
                    "success": has_images,
                    "prompt": prompt,
                    "response_time": round(end_time - start_time, 2),
                    "model": settings.GEMINI_IMAGE_MODEL,
                    "has_images": has_images,
                    "response_keys": list(response.keys()) if response else [],
                    "saved_path": saved_path
                }
                
                if has_images:
                    print(f"✅ 성공 - {result['response_time']}초")
                    print(f"📊 응답 구조: {result['response_keys']}")
                    if saved_path:
                        print(f"💾 저장된 파일: {saved_path}")
                else:
                    print(f"⚠️ 이미지 생성되지 않음 - {result['response_time']}초")
                
                results.append(result)
                
            except GeminiApiError as e:
                print(f"⚠️ Gemini 오류 (예상됨): {e}")
                results.append({
                    "test_number": i,
                    "success": False,
                    "prompt": prompt,
                    "error": str(e),
                    "error_type": "GeminiApiError"
                })
            except Exception as e:
                print(f"❌ 예상치 못한 실패: {e}")
                results.append({
                    "test_number": i,
                    "success": False,
                    "prompt": prompt,
                    "error": str(e),
                    "error_type": "Exception"
                })
        
        return {"test_type": "image_generation", "results": results}
    
    def test_video_generation(self) -> Dict[str, Any]:
        """비디오 생성 테스트"""
        print("\n🎬 Gemini Veo 비디오 생성 테스트")
        print("-" * 40)
        
        test_prompts = [
            "A peaceful ocean wave gently washing over a sandy beach",
            "Cherry blossoms falling in slow motion in a quiet park"
        ]
        
        results = []
        
        for i, prompt in enumerate(test_prompts, 1):
            try:
                print(f"\n📹 테스트 {i}: {prompt}")
                
                start_time = time.time()
                response = self.gemini_api.generate_video(
                    prompt=prompt,
                    duration_seconds=5,
                    aspect_ratio="16:9"
                )
                end_time = time.time()
                
                result = {
                    "test_number": i,
                    "success": True,
                    "prompt": prompt,
                    "response_time": round(end_time - start_time, 2),
                    "model": settings.GEMINI_VIDEO_MODEL,
                    "operation_name": response.get('operation_name'),
                    "status": response.get('status'),
                    "message": response.get('message')
                }
                
                print(f"✅ 비디오 작업 시작 - {result['response_time']}초")
                print(f"🔄 작업 ID: {result['operation_name']}")
                print(f"📄 메시지: {result['message']}")
                
                # 비디오 작업 완료 확인 (짧은 대기 후 한 번만 시도)
                if result['operation_name']:
                    try:
                        print("⏳ 잠시 대기 후 작업 상태 확인...")
                        time.sleep(10)  # 10초 대기
                        
                        operation_result = self.gemini_api.check_video_operation(result['operation_name'])
                        result['operation_status'] = operation_result.get('status')
                        
                        if operation_result.get('done') and operation_result.get('videos'):
                            videos = operation_result['videos']
                            print(f"🎉 비디오 생성 완료! ({len(videos)}개)")
                            
                            # 비디오 저장 시도
                            for idx, video in enumerate(videos):
                                if video.get('video_bytes'):
                                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                                    filename = f"gemini_video_test_{i}_{idx+1}_{timestamp}.mp4"
                                    saved_path = self.save_video_bytes(video['video_bytes'], filename)
                                    if saved_path:
                                        print(f"💾 비디오 저장됨: {saved_path}")
                                        result[f'video_{idx+1}_path'] = saved_path
                        else:
                            print("⏳ 비디오 생성이 아직 진행 중입니다.")
                            
                    except Exception as check_error:
                        print(f"⚠️ 작업 상태 확인 중 오류: {check_error}")
                
                results.append(result)
                
            except GeminiApiError as e:
                print(f"⚠️ Gemini 오류 (예상됨): {e}")
                results.append({
                    "test_number": i,
                    "success": False,
                    "prompt": prompt,
                    "error": str(e),
                    "error_type": "GeminiApiError"
                })
            except Exception as e:
                print(f"❌ 예상치 못한 실패: {e}")
                results.append({
                    "test_number": i,
                    "success": False,
                    "prompt": prompt,
                    "error": str(e),
                    "error_type": "Exception"
                })
        
        return {"test_type": "video_generation", "results": results}
    
    def test_image_analysis(self) -> Dict[str, Any]:
        """이미지 분석 테스트"""
        print("\n👁️ Gemini Vision 이미지 분석 테스트")
        print("-" * 40)
        
        # 테스트용 이미지 URL들
        test_images = [
            {
                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/800px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                "prompt": "이 이미지에서 무엇을 볼 수 있는지 한국어로 자세히 설명해주세요."
            },
            {
                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/React-icon.svg/512px-React-icon.svg.png",
                "prompt": "이 로고가 무엇인지 알려주세요."
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_images, 1):
            try:
                print(f"\n🔍 테스트 {i}: {test_case['url'][:50]}...")
                
                # 이미지를 다운로드하고 base64로 인코딩
                response = requests.get(test_case['url'])
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                
                start_time = time.time()
                analysis_response = self.gemini_api.analyze_image(
                    image_data=image_base64,
                    prompt=test_case['prompt'],
                    mime_type="image/jpeg"
                )
                end_time = time.time()
                
                content = self.gemini_api.extract_text_from_response(analysis_response)
                
                result = {
                    "test_number": i,
                    "success": True,
                    "image_url": test_case['url'],
                    "prompt": test_case['prompt'],
                    "response_time": round(end_time - start_time, 2),
                    "analysis": content,
                    "model": settings.GEMINI_TEXT_MODEL
                }
                
                print(f"✅ 성공 - {result['response_time']}초")
                print(f"📄 분석 결과: {content[:200]}...")
                
                results.append(result)
                
            except Exception as e:
                print(f"❌ 실패: {e}")
                results.append({
                    "test_number": i,
                    "success": False,
                    "image_url": test_case.get('url'),
                    "prompt": test_case.get('prompt'),
                    "error": str(e)
                })
        
        return {"test_type": "image_analysis", "results": results}
    
    def test_speech_generation(self) -> Dict[str, Any]:
        """음성 생성 테스트"""
        print("\n🔊 Gemini TTS 음성 생성 테스트")
        print("-" * 40)
        
        test_texts = [
            "안녕하세요! 저는 Gemini AI입니다.",
            "Today is a beautiful day for testing AI capabilities.",
            "인공지능 기술의 발전은 정말 놀랍습니다."
        ]
        
        results = []
        
        for i, text in enumerate(test_texts, 1):
            try:
                print(f"\n🎙️ 테스트 {i}: {text[:30]}...")
                
                start_time = time.time()
                response = self.gemini_api.generate_speech(
                    text=text,
                    voice="en-US-Journey-D"
                )
                end_time = time.time()
                
                has_audio = bool(response.get('audio_data'))
                saved_path = ""
                
                # 음성이 생성된 경우 저장 시도
                if has_audio:
                    try:
                        audio_data = response.get('audio_data')
                        if audio_data and hasattr(audio_data, 'content') and hasattr(audio_data.content, 'parts'):
                            # audio data에서 바이트 추출
                            for part in audio_data.content.parts:
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    import base64
                                    audio_bytes = base64.b64decode(part.inline_data.data)
                                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                                    filename = f"gemini_speech_test_{i}_{timestamp}.wav"
                                    saved_path = self.save_video_bytes(audio_bytes, filename)  # 음성도 바이너리 데이터이므로 같은 함수 사용
                                    break
                    except Exception as save_error:
                        print(f"⚠️ 음성 저장 중 오류: {save_error}")
                
                result = {
                    "test_number": i,
                    "success": has_audio,
                    "text": text,
                    "response_time": round(end_time - start_time, 2),
                    "has_audio": has_audio,
                    "voice": response.get('voice'),
                    "saved_path": saved_path
                }
                
                if has_audio:
                    print(f"✅ 성공 - {result['response_time']}초")
                    if saved_path:
                        print(f"💾 저장된 파일: {saved_path}")
                else:
                    print(f"⚠️ 음성 생성되지 않음 - {result['response_time']}초")
                
                results.append(result)
                
            except GeminiApiError as e:
                print(f"⚠️ Gemini 오류 (예상됨): {e}")
                results.append({
                    "test_number": i,
                    "success": False,
                    "text": text,
                    "error": str(e),
                    "error_type": "GeminiApiError"
                })
            except Exception as e:
                print(f"❌ 예상치 못한 실패: {e}")
                results.append({
                    "test_number": i,
                    "success": False,
                    "text": text,
                    "error": str(e),
                    "error_type": "Exception"
                })
        
        return {"test_type": "speech_generation", "results": results}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        print("🚀 Gemini API 전체 테스트 시작")
        print("=" * 50)
        
        all_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "api_key_prefix": self.api_key[:10] + "...",
            "model_settings": {
                "text_model": settings.GEMINI_TEXT_MODEL,
                "image_model": settings.GEMINI_IMAGE_MODEL,
                "video_model": settings.GEMINI_VIDEO_MODEL
            },
            "tests": []
        }
        
        # 1. 텍스트 생성 테스트
        text_results = self.test_text_generation()
        all_results["tests"].append(text_results)
        
        # 2. 이미지 분석 테스트
        vision_results = self.test_image_analysis()
        all_results["tests"].append(vision_results)
        
        # 3. 이미지 생성 테스트
        image_results = self.test_image_generation()
        all_results["tests"].append(image_results)
        
        # 4. 비디오 생성 테스트
        video_results = self.test_video_generation()
        all_results["tests"].append(video_results)
        
        # 5. 음성 생성 테스트
        speech_results = self.test_speech_generation()
        all_results["tests"].append(speech_results)
        
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
                    error_type = failed.get('error_type', 'Unknown')
                    if error_type == 'GeminiApiError':
                        print(f"  ⚠️ 테스트 {failed['test_number']}: {failed.get('error', 'Unknown error')[:100]}...")
                    else:
                        print(f"  ❌ 테스트 {failed['test_number']}: {failed.get('error', 'Unknown error')}")
        
        print("\n📝 참고사항:")
        print("- Imagen 및 Veo 기능은 현재 allowlist 기반으로 제한될 수 있습니다.")
        print("- TTS 기능도 일부 사용자에게만 제공될 수 있습니다.")
        print("- 텍스트 생성과 Vision 분석은 일반적으로 사용 가능합니다.")
        
        return all_results


def main():
    """메인 실행 함수"""
    try:
        tester = GeminiTester()
        results = tester.run_all_tests()
        
        print(f"\n✅ 모든 테스트 완료!")
        print(f"📅 실행 시간: {results['timestamp']}")
        
    except KeyboardInterrupt:
        print("\n👋 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    main()
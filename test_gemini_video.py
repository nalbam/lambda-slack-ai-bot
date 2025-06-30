#!/usr/bin/env python3
"""
Gemini Veo 비디오 생성 테스트 스크립트
.env.local의 API 키를 사용하여 비디오 생성을 테스트합니다.
"""

import os
import time
import sys
from pathlib import Path
from typing import Optional

# 프로젝트 루트 경로를 추가하여 src 모듈을 import할 수 있도록 함
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ python-dotenv가 설치되지 않았습니다. 'pip install python-dotenv'로 설치해주세요.")
    sys.exit(1)

# 환경 변수를 먼저 로드해야 합니다
env_file = Path(__file__).parent / ".env.local"
if not env_file.exists():
    print(f"❌ 환경 설정 파일을 찾을 수 없습니다: {env_file}")
    print("📝 .env.example을 참고하여 .env.local 파일을 생성해주세요.")
    sys.exit(1)

load_dotenv(env_file)

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ google-genai가 설치되지 않았습니다. 'pip install google-genai'로 설치해주세요.")
    sys.exit(1)

from src.api.gemini_api import GeminiAPI, GeminiApiError
from src.utils import logger


def load_environment():
    """환경 변수를 로드합니다."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
        print("📝 .env.local 파일에 GEMINI_API_KEY를 추가해주세요.")
        sys.exit(1)

    print(f"✅ 환경 설정 로드 완료 (API 키: {api_key[:10]}...)")
    return api_key


def test_direct_api(api_key: str, prompt: str):
    """google-genai SDK를 직접 사용하여 비디오 생성을 테스트합니다."""
    print("\n🎬 직접 API 테스트 시작...")

    try:
        client = genai.Client(api_key=api_key)

        # Veo 2.0 모델을 사용한 비디오 생성
        config = types.GenerateVideosConfig(
            number_of_videos=1,
            duration_seconds=5,
            enhance_prompt=True,
            aspect_ratio="16:9",
            person_generation="allow_adult"
        )

        print(f"📝 프롬프트: {prompt}")
        print("⏳ 비디오 생성 작업을 시작합니다...")

        operation = client.models.generate_videos(
            model="veo-2.0-generate-001",
            prompt=prompt,
            config=config
        )

        print(f"🔄 작업 ID: {operation.name}")
        print("⏳ 비디오 생성 중... (완료까지 몇 분이 걸릴 수 있습니다)")

        # 작업 완료까지 대기
        max_wait_time = 90  # 1분 30초
        wait_interval = 10  # 10초마다 확인
        elapsed_time = 0

        while not operation.done and elapsed_time < max_wait_time:
            print(f"⏳ 대기 중... ({elapsed_time}초 경과)")
            time.sleep(wait_interval)
            elapsed_time += wait_interval

            try:
                operation = client.operations.get(operation.name)
            except Exception as e:
                print(f"⚠️ 작업 상태 확인 중 오류: {e}")
                continue

        if operation.done:
            print("✅ 비디오 생성 완료!")

            # 결과 처리
            if hasattr(operation, 'result') and operation.result:
                result = operation.result
                if hasattr(result, 'generated_videos') and result.generated_videos:
                    videos = result.generated_videos
                    print(f"📹 생성된 비디오 수: {len(videos)}")

                    for i, video in enumerate(videos):
                        print(f"비디오 {i+1}:")
                        print(f"  - URI: {getattr(video, 'uri', 'N/A')}")
                        print(f"  - 상태: {getattr(video, 'state', 'N/A')}")
                        if hasattr(video, 'video_bytes') and video.video_bytes:
                            print(f"  - 크기: {len(video.video_bytes)} bytes")
                else:
                    print("⚠️ 생성된 비디오가 없습니다.")
            else:
                print("⚠️ 작업 결과를 가져올 수 없습니다.")
        else:
            print(f"⏰ 시간 초과: {max_wait_time}초 후에도 작업이 완료되지 않았습니다.")

    except Exception as e:
        print(f"❌ 직접 API 테스트 실패: {e}")
        if "403" in str(e) or "allowlist" in str(e).lower():
            print("ℹ️ Veo API는 현재 allowlist 뒤에 있어 승인된 개발자만 사용할 수 있습니다.")
        elif "API key" in str(e):
            print("ℹ️ API 키를 확인해주세요.")


def test_wrapper_api(prompt: str):
    """프로젝트의 GeminiAPI 래퍼를 사용하여 비디오 생성을 테스트합니다."""
    print("\n🎬 래퍼 API 테스트 시작...")

    try:
        gemini_api = GeminiAPI()

        result = gemini_api.generate_video(
            prompt=prompt,
            duration_seconds=5,
            aspect_ratio="16:9"
        )

        print("✅ 래퍼 API 호출 성공!")
        print(f"📄 결과: {result}")

        if result.get("status") == "processing":
            print("⏳ 비디오 생성이 시작되었습니다.")
            print(f"🔄 작업 이름: {result.get('operation_name', 'N/A')}")
            print("ℹ️ 실제 비디오 완성을 위해서는 작업 상태를 지속적으로 확인해야 합니다.")

    except GeminiApiError as e:
        print(f"❌ Gemini API 오류: {e}")
    except Exception as e:
        print(f"❌ 래퍼 API 테스트 실패: {e}")


def test_operation_polling(api_key: str, operation_name: str):
    """기존 작업의 상태를 폴링하는 테스트입니다."""
    print(f"\n🔍 작업 상태 확인: {operation_name}")

    try:
        client = genai.Client(api_key=api_key)
        operation = client.operations.get(operation_name)

        print(f"작업 상태: {'완료' if operation.done else '진행 중'}")
        print(f"작업 이름: {operation.name}")

        if operation.done and hasattr(operation, 'result'):
            print("✅ 작업 완료!")
            result = operation.result
            if hasattr(result, 'generated_videos'):
                print(f"생성된 비디오 수: {len(result.generated_videos)}")

    except Exception as e:
        print(f"❌ 작업 상태 확인 실패: {e}")


def main():
    """메인 테스트 함수"""
    print("🎬 Gemini Veo 비디오 생성 테스트")
    print("=" * 50)

    # 환경 변수 로드
    api_key = load_environment()

    # 테스트용 프롬프트
    test_prompts = [
        "A beautiful sunset over a calm ocean with gentle waves",
        "A cute kitten playing with a ball of yarn in a cozy living room",
        "Cherry blossoms falling gently in a peaceful Japanese garden"
    ]

    print("\n📝 사용 가능한 테스트 프롬프트:")
    for i, prompt in enumerate(test_prompts, 1):
        print(f"{i}. {prompt}")

    # 자동으로 첫 번째 프롬프트 선택 (테스트용)
    choice = "1"
    print(f"\n자동 선택: {choice}")

    if choice in ["1", "2", "3"]:
        prompt = test_prompts[int(choice) - 1]
    else:
        print("❌ 잘못된 선택입니다.")
        return

    # 테스트 실행
    print(f"\n🚀 선택된 프롬프트: {prompt}")

    # 1. 래퍼 API 테스트
    test_wrapper_api(prompt)

    # 2. 직접 API 테스트
    test_direct_api(api_key, prompt)

    print("\n✅ 모든 테스트가 완료되었습니다.")
    print("\n📝 참고사항:")
    print("- Veo API는 현재 allowlist 기반으로 운영됩니다.")
    print("- 승인된 개발자만 비디오 생성이 가능합니다.")
    print("- 비디오 생성은 비동기 작업으로 완료까지 시간이 걸립니다.")


if __name__ == "__main__":
    main()

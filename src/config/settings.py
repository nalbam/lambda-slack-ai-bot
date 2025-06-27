"""
설정 및 환경 변수 관리 모듈
"""
import os
from typing import Optional, Dict, Any

# 환경 변수 설정
STAGE = os.environ.get("STAGE", "dev")

# Slack 설정
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"].strip()
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"].strip()
BOT_CURSOR = os.environ.get("BOT_CURSOR", ":robot_face:").strip()

# DynamoDB 설정
BASE_NAME = os.environ.get("BASE_NAME", "slack-ai-bot").strip()
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", f"{BASE_NAME}-{STAGE}").strip()

# OpenAI 설정
OPENAI_ORG_ID = os.environ["OPENAI_ORG_ID"].strip()
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"].strip()
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o").strip() # DO NOT CHANGE THIS

# Gemini 설정 (GEMINI_API_KEY 또는 GOOGLE_API_KEY 사용 가능)
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")).strip()
GEMINI_TEXT_MODEL = os.environ.get("GEMINI_TEXT_MODEL", "gemini-2.5-flash").strip() # DO NOT CHANGE THIS
GEMINI_IMAGE_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "imagen-3.0-generate-002").strip() # DO NOT CHANGE THIS
GEMINI_VIDEO_MODEL = os.environ.get("GEMINI_VIDEO_MODEL", "veo-2.0-generate-001").strip() # DO NOT CHANGE THIS

# 이미지 생성 설정
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "dall-e-3").strip()
IMAGE_QUALITY = os.environ.get("IMAGE_QUALITY", "hd").strip()  # standard, hd
IMAGE_SIZE = os.environ.get("IMAGE_SIZE", "1024x1024").strip()
IMAGE_STYLE = os.environ.get("IMAGE_STYLE", "vivid").strip()  # vivid, natural

# 시스템 메시지
SYSTEM_MESSAGE = os.environ.get("SYSTEM_MESSAGE", "None").strip()

# 생성 설정
TEMPERATURE = float(os.environ.get("TEMPERATURE", 0))

# 메시지 길이 제한
MAX_LEN_SLACK = int(os.environ.get("MAX_LEN_SLACK", 3000))
MAX_LEN_OPENAI = int(os.environ.get("MAX_LEN_OPENAI", 4000))

# 키워드
KEYWARD_IMAGE = os.environ.get("KEYWARD_IMAGE", "그려줘").strip()
KEYWARD_EMOJI = os.environ.get("KEYWARD_EMOJI", "이모지").strip()

# 텍스트 변환 설정
CONVERSION_ARRAY = [
    ["**", "*"],
    # ["#### ", "🔸 "],
    # ["### ", "🔶 "],
    # ["## ", "🟠 "],
    # ["# ", "🟡 "],
]

def validate_env_vars() -> None:
    """필수 환경 변수의 존재 여부를 확인합니다."""
    required_vars = [
        "SLACK_BOT_TOKEN",
        "SLACK_SIGNING_SECRET",
        "OPENAI_API_KEY"
    ]

    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

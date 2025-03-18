"""
설정 및 환경 변수 관리 모듈
"""
import os
from typing import Optional, Dict, Any

# 환경 변수 설정
STAGE = os.environ.get("STAGE", "dev")

# Slack 설정
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
BOT_CURSOR = os.environ.get("BOT_CURSOR", ":robot_face:")

# DynamoDB 설정
BASE_NAME = os.environ.get("BASE_NAME", "slack-ai-bot")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", f"{BASE_NAME}-{STAGE}")

# OpenAI 설정
OPENAI_ORG_ID = os.environ.get("OPENAI_ORG_ID", None)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", None)
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# 이미지 생성 설정
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "dall-e-3")
IMAGE_QUALITY = os.environ.get("IMAGE_QUALITY", "hd")  # standard, hd
IMAGE_SIZE = os.environ.get("IMAGE_SIZE", "1024x1024")
IMAGE_STYLE = os.environ.get("IMAGE_STYLE", "vivid")  # vivid, natural

# 시스템 메시지
SYSTEM_MESSAGE = os.environ.get("SYSTEM_MESSAGE", "None")

# 생성 설정
TEMPERATURE = float(os.environ.get("TEMPERATURE", 0))

# 메시지 길이 제한
MAX_LEN_SLACK = int(os.environ.get("MAX_LEN_SLACK", 3000))
MAX_LEN_OPENAI = int(os.environ.get("MAX_LEN_OPENAI", 4000))

# 키워드
KEYWARD_IMAGE = os.environ.get("KEYWARD_IMAGE", "그려줘")
KEYWARD_EMOJI = os.environ.get("KEYWARD_EMOJI", "이모지")

# 메시지 템플릿
MSG_PREVIOUS = f"이전 대화 내용 확인 중... {BOT_CURSOR}"
MSG_IMAGE_DESCRIBE = f"이미지 감상 중... {BOT_CURSOR}"
MSG_IMAGE_GENERATE = f"이미지 생성 준비 중... {BOT_CURSOR}"
MSG_IMAGE_DRAW = f"이미지 그리는 중... {BOT_CURSOR}"
MSG_RESPONSE = f"응답 기다리는 중... {BOT_CURSOR}"

# 명령어
COMMAND_DESCRIBE = "Describe the image in great detail as if viewing a photo."
COMMAND_GENERATE = "Convert the above sentence into a command for DALL-E to generate an image within 1000 characters. Just give me a prompt."

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

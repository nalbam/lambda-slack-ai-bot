"""
OpenAI API 래퍼 모듈
"""

import functools
from typing import List, Dict, Any, Optional, Generator, Tuple, Union

from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import requests

from src.config import settings
from src.utils import logger

# OpenAI 클라이언트 초기화
openai_client = OpenAI(
    organization=settings.OPENAI_ORG_ID if settings.OPENAI_ORG_ID != "None" else None,
    api_key=settings.OPENAI_API_KEY,
)


class OpenAIApiError(Exception):
    """OpenAI API 오류 클래스"""

    pass


# OpenAI API 호출에 재시도 데코레이터 적용
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(
        (OpenAIApiError, requests.RequestException, ConnectionError)
    ),
    reraise=True,
)
def generate_chat_completion(
    messages: List[Dict[str, str]],
    user: str,
    stream: bool = True,
    temperature: float = settings.TEMPERATURE,
) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
    """OpenAI 채팅 API를 사용하여 응답을 생성합니다.

    Args:
        messages: 대화 메시지 목록 (역할 및 내용)
        user: 사용자 ID
        stream: 스트리밍 사용 여부
        temperature: 생성 온도 (0.0~1.0)

    Returns:
        OpenAI API 응답 또는 스트림 객체

    Raises:
        OpenAIApiError: API 호출 중 오류 발생 시
    """
    try:
        # 메시지가 10건 이상이면 간소화된 로그
        log_messages = messages
        if len(messages) > 10:
            log_messages = [messages[0], "...", messages[-1]]

        logger.log_info(
            f"OpenAI API 요청",
            {
                "model": settings.OPENAI_MODEL,
                "messages_count": len(messages),
                "user": user,
                "stream": stream,
                "temperature": temperature,
            },
        )

        response = openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            stream=stream,
            user=user,
        )

        if not stream:
            usage = getattr(response, "usage", None)
            usage_dict = None
            if usage:
                usage_dict = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(usage, "completion_tokens", 0),
                    "total_tokens": getattr(usage, "total_tokens", 0),
                }

            logger.log_info(
                "OpenAI 채팅 API 응답 수신 완료",
                {
                    "response_id": getattr(response, "id", "unknown"),
                    "usage": usage_dict,
                },
            )
        else:
            logger.log_info("OpenAI 채팅 API 스트리밍 시작")

        return response

    except Exception as e:
        logger.log_error(
            "OpenAI 채팅 API 호출 중 오류 발생",
            e,
            {
                "model": settings.OPENAI_MODEL,
                "messages_count": len(messages),
                "user": user,
                "stream": stream,
            },
        )
        raise OpenAIApiError(f"OpenAI API 오류: {str(e)}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(
        (OpenAIApiError, requests.RequestException, ConnectionError)
    ),
    reraise=True,
)
def generate_image(prompt: str) -> Dict[str, Any]:
    """OpenAI DALL-E API를 사용하여 이미지를 생성합니다.

    Args:
        prompt: 이미지 생성을 위한 프롬프트

    Returns:
        이미지 URL과 수정된 프롬프트를 포함한 결과

    Raises:
        OpenAIApiError: API 호출 중 오류 발생 시
    """
    try:
        logger.log_info(
            f"OpenAI 이미지 생성 요청",
            {
                "model": settings.IMAGE_MODEL,
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "size": settings.IMAGE_SIZE,
                "quality": settings.IMAGE_QUALITY,
            },
        )

        response = openai_client.images.generate(
            model=settings.IMAGE_MODEL,
            prompt=prompt,
            quality=settings.IMAGE_QUALITY,
            size=settings.IMAGE_SIZE,
            style=settings.IMAGE_STYLE,
            n=1,
        )

        result = {
            "image_url": response.data[0].url,
            "revised_prompt": response.data[0].revised_prompt,
        }

        logger.log_debug(
            "OpenAI 이미지 생성 성공",
            {"revised_prompt": response.data[0].revised_prompt[:50] + "..."},
        )

        return result

    except Exception as e:
        logger.log_error(
            "OpenAI 이미지 생성 중 오류 발생",
            e,
            {"prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt},
        )
        raise OpenAIApiError(f"이미지 생성 오류: {str(e)}")

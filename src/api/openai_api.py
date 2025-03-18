"""
OpenAI API 래퍼 모듈
"""
import functools
from typing import List, Dict, Any, Optional, Generator, Tuple, Union

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
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
    retry=retry_if_exception_type((OpenAIApiError, requests.RequestException, ConnectionError)),
    reraise=True
)
def generate_chat_completion(
    messages: List[Dict[str, str]],
    user: str,
    stream: bool = True,
    temperature: float = settings.TEMPERATURE
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
        
        logger.log_debug(f"OpenAI API 요청", {
            "model": settings.OPENAI_MODEL,
            "messages_count": len(messages),
            "messages": log_messages,
            "user": user,
            "stream": stream
        })
        
        response = openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            stream=stream,
            user=user,
        )
        
        return response
        
    except Exception as e:
        logger.log_error("OpenAI 채팅 API 호출 중 오류 발생", e)
        raise OpenAIApiError(f"OpenAI API 오류: {str(e)}")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((OpenAIApiError, requests.RequestException, ConnectionError)),
    reraise=True
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
        logger.log_debug(f"OpenAI 이미지 생성 요청", {
            "model": settings.IMAGE_MODEL,
            "prompt": prompt
        })
        
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
            "revised_prompt": response.data[0].revised_prompt
        }
        
        logger.log_debug("OpenAI 이미지 생성 성공", {
            "revised_prompt": response.data[0].revised_prompt[:50] + "..." 
        })
        
        return result
        
    except Exception as e:
        logger.log_error("OpenAI 이미지 생성 중 오류 발생", e, {
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
        })
        raise OpenAIApiError(f"이미지 생성 오류: {str(e)}")

def extract_content_from_stream(stream: Generator[Dict[str, Any], None, None]) -> Tuple[str, int]:
    """스트림에서 콘텐츠를 추출합니다.
    
    Args:
        stream: OpenAI 스트림 객체
        
    Returns:
        (추출된 텍스트, 추출된 청크 수)의 튜플
    """
    message = ""
    chunk_count = 0
    
    try:
        for chunk in stream:
            chunk_count += 1
            content = chunk.choices[0].delta.content or ""
            message += content
            
        return message, chunk_count
    
    except Exception as e:
        logger.log_error("스트림에서 콘텐츠 추출 중 오류 발생", e)
        return message, chunk_count
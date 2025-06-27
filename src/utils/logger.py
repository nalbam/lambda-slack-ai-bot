"""
로깅 유틸리티 모듈
"""
import logging
import json
from typing import Any, Dict, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 로거 인스턴스 생성
logger = logging.getLogger('lambda-slack-ai-bot')

def log_info(message: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """INFO 레벨 로그를 기록합니다.

    Args:
        message: 로그 메시지
        extra: 추가 로그 데이터 (딕셔너리)
    """
    if extra:
        logger.info(f"{message} - {json.dumps(extra)}")
    else:
        logger.info(message)

def log_error(message: str, error: Optional[Exception] = None, extra: Optional[Dict[str, Any]] = None) -> None:
    """ERROR 레벨 로그를 기록합니다.

    Args:
        message: 에러 메시지
        error: 예외 객체
        extra: 추가 로그 데이터 (딕셔너리)
    """
    if error:
        if extra:
            logger.error(f"{message}: {str(error)} - {json.dumps(extra)}", exc_info=True)
        else:
            logger.error(f"{message}: {str(error)}", exc_info=True)
    else:
        if extra:
            logger.error(f"{message} - {json.dumps(extra)}")
        else:
            logger.error(message)

def log_debug(message: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """DEBUG 레벨 로그를 기록합니다.

    Args:
        message: 로그 메시지
        extra: 추가 로그 데이터 (딕셔너리)
    """
    if extra:
        logger.debug(f"{message} - {json.dumps(extra)}")
    else:
        logger.debug(message)

def log_warning(message: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """WARNING 레벨 로그를 기록합니다.

    Args:
        message: 경고 메시지
        extra: 추가 로그 데이터 (딕셔너리)
    """
    if extra:
        logger.warning(f"{message} - {json.dumps(extra)}")
    else:
        logger.warning(message)

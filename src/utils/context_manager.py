"""
DynamoDB 컨텍스트 관리 유틸리티
"""
import time
import datetime
from typing import Optional, Dict, Any, List
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from src.config import settings
from src.utils import logger

# DynamoDB 리소스 및 테이블 초기화
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(settings.DYNAMODB_TABLE_NAME)

# 캐시 관리 (인메모리 캐싱)
_context_cache = {}

def get_context(thread_ts: Optional[str], user: str, default: str = "") -> str:
    """대화 컨텍스트를 DynamoDB에서 가져옵니다.
    
    Args:
        thread_ts: 스레드 타임스탬프 (None인 경우 DM으로 간주)
        user: 사용자 ID
        default: 컨텍스트가 없을 경우 반환할 기본값
        
    Returns:
        대화 컨텍스트 문자열
    """
    # 캐시 확인
    cache_key = thread_ts if thread_ts else f"dm_{user}"
    if cache_key in _context_cache:
        return _context_cache[cache_key]
    
    try:
        # DynamoDB에서 아이템 조회
        item_id = thread_ts if thread_ts else user
        response = table.get_item(Key={"id": item_id})
        item = response.get("Item")
        
        if item:
            # 캐시에 저장
            _context_cache[cache_key] = item["conversation"]
            return item["conversation"]
        return default
        
    except ClientError as e:
        logger.log_error("DynamoDB에서 컨텍스트 조회 중 오류 발생", e, 
                         {"thread_ts": thread_ts, "user": user})
        return default

def put_context(thread_ts: Optional[str], user: str, conversation: str = "") -> bool:
    """대화 컨텍스트를 DynamoDB에 저장합니다.
    
    Args:
        thread_ts: 스레드 타임스탬프 (None인 경우 DM으로 간주)
        user: 사용자 ID
        conversation: 저장할 대화 컨텍스트
        
    Returns:
        성공 여부
    """
    try:
        # TTL 계산 (1시간)
        expire_at = int(time.time()) + 3600
        expire_dt = datetime.datetime.fromtimestamp(expire_at).isoformat()
        
        # 아이템 준비
        item = {
            "id": thread_ts if thread_ts else user,
            "conversation": conversation,
            "user_id": user,
            "expire_dt": expire_dt,
            "expire_at": expire_at,
        }
        
        # DynamoDB에 저장
        table.put_item(Item=item)
        
        # 캐시 업데이트
        cache_key = thread_ts if thread_ts else f"dm_{user}"
        _context_cache[cache_key] = conversation
        
        return True
        
    except ClientError as e:
        logger.log_error("DynamoDB에 컨텍스트 저장 중 오류 발생", e,
                         {"thread_ts": thread_ts, "user": user})
        return False

def batch_put_contexts(items: List[Dict[str, Any]]) -> None:
    """여러 컨텍스트를 배치로 저장합니다.
    
    Args:
        items: 저장할 아이템 목록
    """
    try:
        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)
                
        # 캐시 업데이트
        for item in items:
            thread_ts = item.get("id")
            user = item.get("user_id")
            conversation = item.get("conversation")
            if thread_ts and user and conversation:
                cache_key = thread_ts if thread_ts != user else f"dm_{user}"
                _context_cache[cache_key] = conversation
                
    except ClientError as e:
        logger.log_error("DynamoDB 배치 저장 중 오류 발생", e)

def clear_cache() -> None:
    """컨텍스트 캐시를 비웁니다."""
    global _context_cache
    _context_cache = {}
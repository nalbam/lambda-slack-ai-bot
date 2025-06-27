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

# DynamoDB 리소스 초기화
dynamodb = boto3.resource("dynamodb")
dynamodb_client = boto3.client('dynamodb')
table = dynamodb.Table(settings.DYNAMODB_TABLE_NAME)

# 캐시 관리 (인메모리 캐싱)
_context_cache = {}

def check_table_exists() -> bool:
    """DynamoDB 테이블이 존재하는지 확인합니다.

    Returns:
        테이블 존재 여부
    """
    try:
        logger.log_info(f"DynamoDB 테이블 확인: {settings.DYNAMODB_TABLE_NAME}")
        response = dynamodb_client.describe_table(TableName=settings.DYNAMODB_TABLE_NAME)
        table_status = response['Table']['TableStatus']
        logger.log_info(f"DynamoDB 테이블 상태: {table_status}", {
            "table_name": settings.DYNAMODB_TABLE_NAME
        })
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.log_error(f"DynamoDB 테이블을 찾을 수 없음", e, {
                "table_name": settings.DYNAMODB_TABLE_NAME
            })
            return False
        else:
            logger.log_error(f"DynamoDB 테이블 확인 중 오류 발생", e, {
                "table_name": settings.DYNAMODB_TABLE_NAME
            })
            return False

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
        logger.log_debug("캐시에서 컨텍스트 조회됨", {"cache_key": cache_key})
        return _context_cache[cache_key]

    try:
        # DynamoDB에서 아이템 조회
        item_id = thread_ts if thread_ts else user
        logger.log_debug("DynamoDB 컨텍스트 조회 시도", {
            "item_id": item_id,
            "table_name": settings.DYNAMODB_TABLE_NAME
        })

        response = table.get_item(Key={"id": item_id})
        item = response.get("Item")

        if item:
            # 캐시에 저장
            _context_cache[cache_key] = item["conversation"]
            logger.log_debug("DynamoDB에서 컨텍스트 조회됨", {"item_id": item_id})
            return item["conversation"]

        logger.log_debug("DynamoDB에서 컨텍스트를 찾을 수 없음", {"item_id": item_id})
        return default

    except ClientError as e:
        error_code = e.response['Error']['Code'] if 'Error' in e.response else 'Unknown'
        error_msg = e.response['Error']['Message'] if 'Error' in e.response else str(e)

        logger.log_error(f"DynamoDB 컨텍스트 조회 중 오류 발생: {error_code}", e, {
            "thread_ts": thread_ts,
            "user": user,
            "table_name": settings.DYNAMODB_TABLE_NAME,
            "error": error_msg
        })
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
        item_id = thread_ts if thread_ts else user
        item = {
            "id": item_id,
            "conversation": conversation,
            "user_id": user,
            "expire_dt": expire_dt,
            "expire_at": expire_at,
        }

        logger.log_debug("DynamoDB에 컨텍스트 저장 시도", {
            "item_id": item_id,
            "table_name": settings.DYNAMODB_TABLE_NAME
        })

        # DynamoDB에 저장
        table.put_item(Item=item)

        # 캐시 업데이트
        cache_key = thread_ts if thread_ts else f"dm_{user}"
        _context_cache[cache_key] = conversation

        logger.log_debug("DynamoDB에 컨텍스트 저장 성공", {"item_id": item_id})
        return True

    except ClientError as e:
        error_code = e.response['Error']['Code'] if 'Error' in e.response else 'Unknown'
        error_msg = e.response['Error']['Message'] if 'Error' in e.response else str(e)

        logger.log_error(f"DynamoDB에 컨텍스트 저장 중 오류 발생: {error_code}", e, {
            "thread_ts": thread_ts,
            "user": user,
            "table_name": settings.DYNAMODB_TABLE_NAME,
            "error": error_msg
        })
        return False


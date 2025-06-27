"""
Lambda Slack AI Bot - Lambda 핸들러
4단계 워크플로우 엔진 통합 완료:
1. 사용자 의도 파악 (OpenAI 분석)
2. 작업 나열 (실행 계획 수립)
3. 작업 처리 및 즉시 회신 (AI 요약 없이 직접 전송)
4. 완료 알림
"""
import json
import sys
from typing import Dict, Any, Optional

from slack_bolt.adapter.aws_lambda import SlackRequestHandler

from src.config import settings
from src.utils import logger, context_manager
from src.api import slack_api
from src.handlers.message_handler import MessageHandler

# 환경 변수 검증
settings.validate_env_vars()

# DynamoDB 테이블 확인
context_manager.check_table_exists()

# Slack 앱 초기화
app = slack_api.initialize_slack_app()

# Slack 핸들러 초기화
slack_handler = SlackRequestHandler(app=app)

# 메시지 핸들러 초기화
message_handler = MessageHandler(app)

# Bot ID 저장
bot_id = slack_api.get_bot_id(app)

# 이벤트 핸들러 등록
@app.event("app_mention")
def handle_mention(body: Dict[str, Any], say):
    """앱 멘션 이벤트 핸들러 - 4단계 워크플로우 지원"""
    try:
        event = body.get("event", {})
        logger.log_info("앱 멘션 이벤트 처리", {
            "event_id": body.get("event_id"),
            "text": event.get("text", "")[:100],  # 처음 100자만 로깅
            "workflow_capable": True
        })
        message_handler.handle_mention(body, say)
    except Exception as e:
        logger.log_error("앱 멘션 처리 중 오류 발생", e)

@app.event("message")
def handle_message(body: Dict[str, Any], say):
    """메시지 이벤트 핸들러 - 4단계 워크플로우 지원"""
    try:
        event = body.get("event", {})

        # 봇 메시지 무시
        if "bot_id" in event:
            return

        logger.log_info("메시지 이벤트 처리", {
            "event_id": body.get("event_id"),
            "text": event.get("text", "")[:100],  # 처음 100자만 로깅
            "workflow_capable": True
        })
        message_handler.handle_message(body, say)
    except Exception as e:
        logger.log_error("메시지 처리 중 오류 발생", e)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda 함수 핸들러

    Args:
        event: Lambda 이벤트 데이터
        context: Lambda 컨텍스트

    Returns:
        Lambda 응답
    """
    try:
        logger.log_info("Lambda 함수 시작", {
            "request_id": context.aws_request_id,
            "function_name": context.function_name,
            "remaining_time": context.get_remaining_time_in_millis()
        })
        # JSON 파싱
        if "body" in event:
            body = json.loads(event["body"])

            # Slack 이벤트 확인 요청 처리
            if "challenge" in body:
                logger.log_info("Slack 이벤트 확인 요청 처리")
                return {
                    "statusCode": 200,
                    "headers": {"Content-type": "application/json"},
                    "body": json.dumps({"challenge": body["challenge"]}),
                }

            # 이벤트 검증
            if "event" not in body or "client_msg_id" not in body.get("event", {}):
                logger.log_info("이벤트 데이터 누락 또는 중복 요청")
                return {
                    "statusCode": 200,
                    "headers": {"Content-type": "application/json"},
                    "body": json.dumps({"status": "Success"}),
                }

            # 중복 요청 방지를 위한 컨텍스트 확인
            token = body["event"]["client_msg_id"]
            user = body["event"]["user"]
            prompt = context_manager.get_context(token, user)

            if prompt != "":
                logger.log_info("중복 요청 감지", {"token": token, "user": user})
                return {
                    "statusCode": 200,
                    "headers": {"Content-type": "application/json"},
                    "body": json.dumps({"status": "Success"}),
                }

            # 컨텍스트 저장
            context_manager.put_context(token, user, body["event"]["text"])

        # Slack 이벤트 처리
        result = slack_handler.handle(event, context)
        logger.log_info("Lambda 함수 완료", {
            "status_code": result.get("statusCode", 200),
            "remaining_time": context.get_remaining_time_in_millis()
        })
        return result

    except Exception as e:
        logger.log_error("Lambda 핸들러 오류", e, {
            "request_id": context.aws_request_id,
            "function_name": context.function_name,
            "remaining_time": context.get_remaining_time_in_millis()
        })

        return {
            "statusCode": 500,
            "headers": {"Content-type": "application/json"},
            "body": json.dumps({"status": "Error", "message": str(e)}),
        }

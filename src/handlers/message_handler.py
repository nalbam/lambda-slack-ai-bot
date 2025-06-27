"""
새로운 Slack 메시지 처리 핸들러 - 워크플로우 중심 설계
"""
from typing import Dict, Any, List

from slack_bolt import App, Say

from src.utils import logger
from src.api import slack_api


class MessageHandler:
    """5단계 워크플로우 중심의 Slack 메시지 처리 핸들러"""

    def __init__(self, app: App):
        """
        Args:
            app: Slack 앱 인스턴스
        """
        self.app = app
        self.bot_id = slack_api.get_bot_id(app)

    def handle_mention(self, body: Dict[str, Any], say: Say) -> None:
        """앱 멘션 이벤트 핸들러 - 워크플로우 엔진으로 처리

        Args:
            body: 이벤트 본문
            say: Slack Say 객체
        """
        event = body.get("event", {})
        parsed_event = slack_api.parse_slack_event(event, self.bot_id)
        
        try:
            # 컨텍스트 준비
            context = self._prepare_context(parsed_event, event)
            
            # Slack 컨텍스트 준비
            slack_context = {
                'app': self.app,
                'say': say,
                'channel': parsed_event["channel"],
                'thread_ts': parsed_event["thread_ts"],
                'user_id': parsed_event["user"]
            }
            
            # 워크플로우 엔진으로 처리
            self._process_with_workflow(parsed_event["text"], context, slack_context)
            
        except Exception as e:
            logger.log_error("멘션 처리 실패", e)
            self._send_error_message(say, parsed_event.get("thread_ts"), 
                                   "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.")

    def handle_message(self, body: Dict[str, Any], say: Say) -> None:
        """다이렉트 메시지 이벤트 핸들러 - 워크플로우 엔진으로 처리

        Args:
            body: 이벤트 본문
            say: Slack Say 객체
        """
        event = body.get("event", {})

        # 봇 메시지 무시
        if "bot_id" in event:
            return

        parsed_event = slack_api.parse_slack_event(event, self.bot_id)
        
        try:
            # 컨텍스트 준비 (DM은 스레드 없음)
            parsed_event["thread_ts"] = None  # DM은 스레드 없음
            context = self._prepare_context(parsed_event, event)
            
            # Slack 컨텍스트 준비
            slack_context = {
                'app': self.app,
                'say': say,
                'channel': parsed_event["channel"],
                'thread_ts': None,  # DM은 스레드 없음
                'user_id': parsed_event["user"]
            }
            
            # 워크플로우 엔진으로 처리
            self._process_with_workflow(parsed_event["text"], context, slack_context)
            
        except Exception as e:
            logger.log_error("DM 처리 실패", e)
            self._send_error_message(say, None, 
                                   "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.")

    def _prepare_context(self, parsed_event: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로우를 위한 컨텍스트 준비"""
        
        context = {
            'user_id': parsed_event["user"],
            'user_name': slack_api.get_user_display_name(self.app, parsed_event["user"]),
            'client_msg_id': parsed_event["client_msg_id"],
            'thread_length': 0,
            'uploaded_image': None,
            'thread_messages': []
        }
        
        # 스레드 컨텍스트 준비
        if parsed_event.get("thread_ts"):
            try:
                thread_messages = self._process_thread_messages(
                    parsed_event["channel"], 
                    parsed_event["thread_ts"], 
                    parsed_event["client_msg_id"]
                )
                context['thread_messages'] = thread_messages
                context['thread_length'] = len(thread_messages)
            except Exception as e:
                logger.log_error("스레드 컨텍스트 준비 실패", e)
        
        # 업로드된 이미지 처리
        if "files" in event:
            files = event.get("files", [])
            for file in files:
                mimetype = file.get("mimetype", "")
                if mimetype and mimetype.startswith("image"):
                    # 이미지 정보 저장
                    context['uploaded_image'] = {
                        'url': file.get("url_private"),
                        'mimetype': mimetype,
                        'name': file.get("name", "image.png")
                    }
                    
                    # base64 인코딩 시도
                    try:
                        base64_data = slack_api.get_encoded_image_from_slack(file.get("url_private"))
                        if base64_data:
                            context['uploaded_image']['base64'] = base64_data
                    except Exception as e:
                        logger.log_error("이미지 인코딩 실패", e)
                    
                    break  # 첫 번째 이미지만 처리
        
        return context

    def _process_thread_messages(self, channel: str, thread_ts: str, client_msg_id: str) -> List[Dict[str, str]]:
        """스레드 메시지를 처리하여 OpenAI 메시지 형식으로 변환"""
        
        messages = []
        
        try:
            # 스레드 메시지 가져오기
            thread_messages = slack_api.get_thread_messages(self.app, channel, thread_ts, client_msg_id)
            
            # 메시지 처리
            for message in thread_messages:
                # 역할 결정
                role = "assistant" if message.get("bot_id", "") else "user"
                
                # 사용자 이름 가져오기
                user_name = slack_api.get_user_display_name(self.app, message.get("user"))
                
                # 메시지 추가
                messages.append({
                    "role": role,
                    "content": f"{user_name}: {message.get('text', '')}"
                })
        
        except Exception as e:
            logger.log_error("스레드 메시지 처리 중 오류 발생", e)
        
        return messages

    def _process_with_workflow(self, user_message: str, context: Dict[str, Any], slack_context: Dict[str, Any]) -> None:
        """워크플로우 엔진으로 요청 처리"""
        
        try:
            from src.workflow.workflow_engine import WorkflowEngine
            
            engine = WorkflowEngine(self.app, slack_context)
            engine.process_user_request(user_message, context)
            
        except Exception as e:
            logger.log_error("워크플로우 엔진 실행 실패", e)
            # 최후 수단: 간단한 에러 메시지
            self._send_error_message(
                slack_context["say"], 
                slack_context.get("thread_ts"),
                "요청을 처리할 수 없습니다. 잠시 후 다시 시도해 주세요."
            )

    def _send_error_message(self, say: Say, thread_ts: str, message: str) -> None:
        """에러 메시지 전송"""
        
        try:
            say(text=f"⚠️ {message}", thread_ts=thread_ts)
        except Exception as e:
            logger.log_error("에러 메시지 전송 실패", e)
"""
Slack 메시지 처리 유틸리티 - 기존 로직 통합
"""
import sys
from typing import Dict, Any, List, Tuple

from slack_bolt import App, Say

from src.config import settings
from src.utils import logger
from src.api import slack_api, openai_api


class SlackMessageUtils:
    """Slack 메시지 처리를 위한 유틸리티 클래스"""

    def __init__(self, app: App):
        self.app = app

    def chat_update(self, say: Say, channel: str, thread_ts: str, latest_ts: str,
                   message: str, continue_thread: bool = False) -> Tuple[str, str]:
        """메시지를 Slack에 업데이트합니다."""
        
        try:
            # 메시지 길이 제한 확인
            if sys.getsizeof(message) > settings.MAX_LEN_SLACK:
                # 코드 블록으로 분할하는 것이 가능한지 확인
                split_key = "\n\n"
                if "```" in message:
                    split_key = "```"

                parts = message.split(split_key)
                last_one = parts.pop()

                # 분할 균형 확인
                if len(parts) % 2 == 0:
                    text = split_key.join(parts) + split_key
                    message = last_one
                else:
                    text = split_key.join(parts)
                    message = split_key + last_one

                # 텍스트 포맷팅 및 업데이트
                text = slack_api.replace_text(text)
                slack_api.update_message(self.app, channel, latest_ts, text)

                # 계속 진행 중인 경우 커서 추가
                if continue_thread:
                    text = f"{slack_api.replace_text(message)} {settings.BOT_CURSOR}"
                else:
                    text = slack_api.replace_text(message)

                # 새 메시지 전송
                result = say(text=text, thread_ts=thread_ts)
                latest_ts = result["ts"]
            else:
                # 계속 진행 중인 경우 커서 추가
                if continue_thread:
                    text = f"{slack_api.replace_text(message)} {settings.BOT_CURSOR}"
                else:
                    text = slack_api.replace_text(message)

                # 메시지 업데이트
                slack_api.update_message(self.app, channel, latest_ts, text)

            return message, latest_ts

        except Exception as e:
            logger.log_error("메시지 업데이트 중 오류 발생", e, {
                "channel": channel,
                "thread_ts": thread_ts,
                "latest_ts": latest_ts
            })
            return message, latest_ts

    def reply_text_stream(self, messages: List[Dict[str, str]], say: Say, channel: str,
                         thread_ts: str, latest_ts: str, user: str) -> str:
        """스트리밍으로 텍스트 응답을 생성하고 전송합니다."""
        
        try:
            # OpenAI API 스트림 생성
            stream = openai_api.generate_chat_completion(
                messages=messages,
                user=user,
                stream=True
            )

            counter = 0
            message = ""
            buffer_size = 0
            update_threshold = 800  # 약 800자마다 업데이트

            # 스트림에서 응답 처리
            for part in stream:
                reply = part.choices[0].delta.content or ""

                if reply:
                    message += reply
                    buffer_size += len(reply)

                # 버퍼 크기 또는 카운터 기반으로 업데이트
                if buffer_size >= update_threshold or (counter > 0 and counter % 24 == 0):
                    message, latest_ts = self.chat_update(
                        say, channel, thread_ts, latest_ts, message, True
                    )
                    buffer_size = 0

                counter += 1

            # 최종 메시지 업데이트
            self.chat_update(say, channel, thread_ts, latest_ts, message)

            return message

        except Exception as e:
            logger.log_error("스트리밍 텍스트 응답 생성 중 오류 발생", e)
            error_message = f"```오류 발생: {str(e)}```"
            self.chat_update(say, channel, thread_ts, latest_ts, error_message)
            return error_message

    def upload_image_to_slack(self, say: Say, channel: str, thread_ts: str, latest_ts: str,
                             image_data: bytes, filename: str, prompt: str = "") -> str:
        """이미지를 Slack에 업로드합니다."""
        
        try:
            # 파일 업로드
            slack_api.upload_file(
                self.app, channel, image_data, filename, thread_ts
            )

            # 프롬프트가 있는 경우 업데이트
            if prompt:
                self.chat_update(say, channel, thread_ts, latest_ts, prompt)

            return "이미지 업로드 완료"

        except Exception as e:
            logger.log_error("이미지 업로드 중 오류 발생", e)
            error_message = f"```이미지 업로드 오류: {str(e)}```"
            self.chat_update(say, channel, thread_ts, latest_ts, error_message)
            return error_message
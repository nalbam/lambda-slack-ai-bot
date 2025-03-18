"""
Slack 메시지 처리 핸들러
"""
import sys
from typing import Dict, Any, List, Optional, Tuple, Union

from slack_bolt import App, Say

from src.config import settings
from src.utils import logger
from src.api import slack_api, openai_api
from src.utils import context_manager

class MessageHandler:
    """Slack 메시지 처리 핸들러 클래스"""
    
    def __init__(self, app: App):
        """
        Args:
            app: Slack 앱 인스턴스
        """
        self.app = app
        self.bot_id = slack_api.get_bot_id(app)
        
    def chat_update(self, say: Say, channel: str, thread_ts: str, latest_ts: str, 
                   message: str, continue_thread: bool = False) -> Tuple[str, str]:
        """메시지를 Slack에 업데이트합니다.
        
        Args:
            say: Slack Say 객체
            channel: 채널 ID
            thread_ts: 스레드 타임스탬프
            latest_ts: 최신 메시지 타임스탬프
            message: 메시지 내용
            continue_thread: 계속 진행 중인지 여부
            
        Returns:
            (메시지, 새 타임스탬프) 튜플
        """
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

    def reply_text(self, messages: List[Dict[str, str]], say: Say, channel: str, 
                  thread_ts: str, latest_ts: str, user: str) -> str:
        """텍스트 응답을 생성하고 전송합니다.
        
        Args:
            messages: 대화 메시지 목록
            say: Slack Say 객체
            channel: 채널 ID
            thread_ts: 스레드 타임스탬프
            latest_ts: 최신 메시지 타임스탬프
            user: 사용자 ID
            
        Returns:
            생성된 응답 메시지
        """
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
            logger.log_error("텍스트 응답 생성 중 오류 발생", e)
            error_message = f"```오류 발생: {str(e)}```"
            self.chat_update(say, channel, thread_ts, latest_ts, error_message)
            return error_message

    def reply_image(self, prompt: str, say: Say, channel: str, thread_ts: str, latest_ts: str) -> str:
        """이미지를 생성하고 전송합니다.
        
        Args:
            prompt: 이미지 생성 프롬프트
            say: Slack Say 객체
            channel: 채널 ID
            thread_ts: 스레드 타임스탬프
            latest_ts: 최신 메시지 타임스탬프
            
        Returns:
            이미지 URL
        """
        try:
            # 이미지 생성
            image_result = openai_api.generate_image(prompt)
            
            image_url = image_result["image_url"]
            revised_prompt = image_result["revised_prompt"]
            
            # 이미지 다운로드
            file_ext = image_url.split(".")[-1].split("?")[0]
            filename = f"{settings.IMAGE_MODEL}.{file_ext}"
            
            file_data = slack_api.get_image_from_slack(image_url)
            if not file_data:
                # 직접 다운로드 시도
                try:
                    import requests
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        file_data = response.content
                except Exception as e:
                    logger.log_error("이미지 다운로드 중 오류 발생", e)
                    self.chat_update(say, channel, thread_ts, latest_ts, "이미지를 다운로드할 수 없습니다.")
                    return ""
            
            # 파일 업로드
            slack_api.upload_file(
                self.app, channel, file_data, filename, thread_ts
            )
            
            # 프롬프트 업데이트
            self.chat_update(say, channel, thread_ts, latest_ts, revised_prompt)
            
            return image_url
            
        except Exception as e:
            logger.log_error("이미지 응답 생성 중 오류 발생", e)
            error_message = f"```이미지 생성 오류: {str(e)}```"
            self.chat_update(say, channel, thread_ts, latest_ts, error_message)
            return ""

    def process_thread_messages(self, channel: str, thread_ts: str, client_msg_id: str, 
                              type_keyword: Optional[str] = None) -> List[Dict[str, str]]:
        """스레드 메시지를 처리하여 OpenAI 메시지 형식으로 변환합니다.
        
        Args:
            channel: 채널 ID
            thread_ts: 스레드 타임스탬프
            client_msg_id: 클라이언트 메시지 ID
            type_keyword: 메시지 유형 키워드 (선택 사항)
            
        Returns:
            OpenAI 메시지 형식의 목록
        """
        messages = []
        
        try:
            # 스레드 메시지 가져오기
            thread_messages = slack_api.get_thread_messages(self.app, channel, thread_ts, client_msg_id)
            
            # 첫 번째 메시지의 타임스탬프
            first_ts = thread_messages[0].get("ts") if thread_messages else None
            
            # 메시지 처리
            for message in thread_messages:
                # 역할 결정
                role = "assistant" if message.get("bot_id", "") else "user"
                
                # 이모지 키워드가 있고 첫 번째 메시지에 리액션이 있는 경우
                if type_keyword == "emoji" and first_ts == message.get("ts") and "reactions" in message:
                    reactions = slack_api.get_reactions(self.app, message.get("reactions", []))
                    if reactions:
                        messages.append({
                            "role": role,
                            "content": f"reactions {reactions}"
                        })
                
                # 사용자 이름 가져오기
                user_name = slack_api.get_user_display_name(self.app, message.get("user"))
                
                # 메시지 추가
                messages.append({
                    "role": role,
                    "content": f"{user_name}: {message.get('text', '')}"
                })
                
                # 메시지 크기 제한 확인
                if sys.getsizeof(messages) > settings.MAX_LEN_OPENAI:
                    messages.pop(0)  # 가장 오래된 메시지 제거
                    break
            
            # 시스템 메시지 추가
            if settings.SYSTEM_MESSAGE != "None":
                messages.append({
                    "role": "system",
                    "content": settings.SYSTEM_MESSAGE
                })
            
            return messages
            
        except Exception as e:
            logger.log_error("스레드 메시지 처리 중 오류 발생", e, {
                "channel": channel,
                "thread_ts": thread_ts
            })
            return messages

    def content_from_message(self, text: str, event: Dict[str, Any], user: str) -> Tuple[List[Dict[str, Any]], str]:
        """메시지 내용을 OpenAI API 형식으로 변환합니다.
        
        Args:
            text: 메시지 텍스트
            event: Slack 이벤트 데이터
            user: 사용자 ID
            
        Returns:
            (OpenAI API 형식의 콘텐츠, 메시지 유형) 튜플
        """
        # 메시지 유형 결정
        content_type = "text"
        
        if settings.KEYWARD_IMAGE in text:
            content_type = "image"
        elif settings.KEYWARD_EMOJI in text:
            content_type = "emoji"
            text = slack_api.replace_emoji_pattern(text)
        
        # 사용자 이름 가져오기
        user_name = slack_api.get_user_display_name(self.app, user)
        
        # 기본 텍스트 콘텐츠 추가
        content = [{"type": "text", "text": f"{user_name}: {text}"}]
        
        # 첨부 파일 처리
        if "files" in event:
            files = event.get("files", [])
            for file in files:
                mimetype = file.get("mimetype", "")
                if mimetype and mimetype.startswith("image"):
                    image_url = file.get("url_private")
                    base64_image = slack_api.get_encoded_image_from_slack(image_url)
                    if base64_image:
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mimetype};base64,{base64_image}"
                            }
                        })
        
        return content, content_type

    def conversation(self, say: Say, thread_ts: Optional[str], content: List[Dict[str, Any]], 
                   channel: str, user: str, client_msg_id: str, type_keyword: Optional[str] = None) -> None:
        """대화 처리 메인 함수입니다.
        
        Args:
            say: Slack Say 객체
            thread_ts: 스레드 타임스탬프 (없는 경우 DM)
            content: 메시지 콘텐츠
            channel: 채널 ID
            user: 사용자 ID
            client_msg_id: 클라이언트 메시지 ID
            type_keyword: 메시지 유형 키워드 (선택 사항)
        """
        logger.log_debug("대화 처리 시작", {"content": content, "thread_ts": thread_ts})
        
        # 초기 메시지와 타임스탬프
        result = say(text=settings.BOT_CURSOR, thread_ts=thread_ts)
        latest_ts = result["ts"]
        
        # OpenAI API 메시지 형식 준비
        messages = [{"role": "user", "content": content}]
        
        # 스레드 메시지 처리
        if thread_ts:
            self.chat_update(say, channel, thread_ts, latest_ts, settings.MSG_PREVIOUS)
            thread_messages = self.process_thread_messages(channel, thread_ts, client_msg_id, type_keyword)
            
            # 역순으로 변환하여 시간 순서대로 정렬
            messages = thread_messages[::-1] + messages
        
        try:
            logger.log_debug("OpenAI API 요청 준비", {"messages_count": len(messages)})
            
            # OpenAI API 호출 및 응답 처리
            self.chat_update(say, channel, thread_ts, latest_ts, settings.MSG_RESPONSE)
            message = self.reply_text(messages, say, channel, thread_ts, latest_ts, user)
            
            logger.log_debug("응답 생성 완료", {"response_length": len(message)})
            
        except Exception as e:
            logger.log_error("대화 처리 중 오류 발생", e)
            error_message = f"```오류 발생: {str(e)}```"
            self.chat_update(say, channel, thread_ts, latest_ts, error_message)

    def image_generate(self, say: Say, thread_ts: Optional[str], content: List[Dict[str, Any]], 
                      channel: str, client_msg_id: str, type_keyword: Optional[str] = None) -> None:
        """이미지 생성 처리 메인 함수입니다.
        
        Args:
            say: Slack Say 객체
            thread_ts: 스레드 타임스탬프 (없는 경우 DM)
            content: 메시지 콘텐츠
            channel: 채널 ID
            client_msg_id: 클라이언트 메시지 ID
            type_keyword: 메시지 유형 키워드 (선택 사항)
        """
        logger.log_debug("이미지 생성 처리 시작", {"content_type": type_keyword})
        
        # 초기 메시지와 타임스탬프
        result = say(text=settings.BOT_CURSOR, thread_ts=thread_ts)
        latest_ts = result["ts"]
        
        # 기본 프롬프트 추출
        prompt = content[0]["text"]
        prompts = []
        
        # 스레드 메시지 처리
        if thread_ts:
            self.chat_update(say, channel, thread_ts, latest_ts, settings.MSG_PREVIOUS)
            
            # 스레드 메시지 가져오기
            thread_messages = self.process_thread_messages(channel, thread_ts, client_msg_id, type_keyword)
            thread_messages = thread_messages[::-1]  # 역순으로 변환
            
            # 프롬프트 형식으로 변환
            prompts = [
                f"{msg['role']}: {msg['content']}" 
                for msg in thread_messages 
                if msg['content'].strip()
            ]
        
        # 이미지 콘텐츠 처리
        if len(content) > 1:
            self.chat_update(say, channel, thread_ts, latest_ts, settings.MSG_IMAGE_DESCRIBE)
            
            # 이미지 묘사 요청
            try:
                content_copy = content.copy()
                content_copy[0]["text"] = settings.COMMAND_DESCRIBE
                
                # 이미지 묘사 요청
                response = openai_api.generate_chat_completion(
                    messages=[{"role": "user", "content": content_copy}],
                    user=client_msg_id,
                    stream=False
                )
                
                # 묘사 내용 추가
                image_description = response.choices[0].message.content
                prompts.append(image_description)
                
            except Exception as e:
                logger.log_error("이미지 묘사 중 오류 발생", e)
        
        # 기본 프롬프트 추가
        prompts.append(prompt)
        
        # 이미지 생성 프롬프트 준비
        try:
            self.chat_update(say, channel, thread_ts, latest_ts, settings.MSG_IMAGE_GENERATE)
            
            # DALL-E 프롬프트 준비
            prompts.append(settings.COMMAND_GENERATE)
            
            # OpenAI API를 통해 DALL-E 프롬프트 생성
            response = openai_api.generate_chat_completion(
                messages=[{
                    "role": "user",
                    "content": [{"type": "text", "text": "\n\n\n".join(prompts)}]
                }],
                user=client_msg_id,
                stream=False
            )
            
            # 최종 DALL-E 프롬프트
            dalle_prompt = response.choices[0].message.content
            
            # 프롬프트 표시
            self.chat_update(say, channel, thread_ts, latest_ts, f"{dalle_prompt} {settings.BOT_CURSOR}")
            
            # 이미지 생성 및 업로드
            self.reply_image(dalle_prompt, say, channel, thread_ts, latest_ts)
            
        except Exception as e:
            logger.log_error("이미지 생성 프롬프트 준비 중 오류 발생", e)
            error_message = f"```이미지 생성 오류: {str(e)}```"
            self.chat_update(say, channel, thread_ts, latest_ts, error_message)

    def handle_mention(self, body: Dict[str, Any], say: Say) -> None:
        """앱 멘션 이벤트 핸들러입니다.
        
        Args:
            body: 이벤트 본문
            say: Slack Say 객체
        """
        event = body.get("event", {})
        
        # 이벤트 파싱
        parsed_event = slack_api.parse_slack_event(event, self.bot_id)
        thread_ts = parsed_event["thread_ts"]
        text = parsed_event["text"]
        channel = parsed_event["channel"]
        user = parsed_event["user"]
        client_msg_id = parsed_event["client_msg_id"]
        
        # 메시지 콘텐츠 준비
        content, content_type = self.content_from_message(text, event, user)
        
        # 이미지 생성 또는 대화 처리
        if content_type == "image":
            self.image_generate(say, thread_ts, content, channel, client_msg_id, content_type)
        else:
            self.conversation(say, thread_ts, content, channel, user, client_msg_id, content_type)

    def handle_message(self, body: Dict[str, Any], say: Say) -> None:
        """다이렉트 메시지 이벤트 핸들러입니다.
        
        Args:
            body: 이벤트 본문
            say: Slack Say 객체
        """
        event = body.get("event", {})
        
        # 봇 메시지 무시
        if "bot_id" in event:
            return
        
        # 이벤트 파싱
        parsed_event = slack_api.parse_slack_event(event, self.bot_id)
        text = parsed_event["text"]
        channel = parsed_event["channel"]
        user = parsed_event["user"]
        client_msg_id = parsed_event["client_msg_id"]
        
        # DM은 스레드 없음
        thread_ts = None
        
        # 메시지 콘텐츠 준비
        content, content_type = self.content_from_message(text, event, user)
        
        # 이미지 생성 또는 대화 처리
        if content_type == "image":
            self.image_generate(say, thread_ts, content, channel, client_msg_id, content_type)
        else:
            self.conversation(say, thread_ts, content, channel, user, client_msg_id, content_type)
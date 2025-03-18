"""
Slack API 래퍼 모듈
"""
import re
import functools
import requests
import base64
from typing import Dict, Any, List, Optional, Tuple, Callable

from slack_bolt import App, Say
from slack_sdk.errors import SlackApiError

from src.config import settings
from src.utils import logger

# 사용자 정보 캐시
_user_info_cache = {}

class SlackApiError(Exception):
    """Slack API 오류 클래스"""
    pass

def initialize_slack_app() -> App:
    """Slack 앱을 초기화합니다.

    Returns:
        초기화된 Slack 앱 인스턴스
    """
    app = App(
        token=settings.SLACK_BOT_TOKEN,
        signing_secret=settings.SLACK_SIGNING_SECRET,
        process_before_response=True,
    )

    try:
        # Slack API 연결 확인 및 봇 ID 가져오기
        auth_test = app.client.api_call("auth.test")
        bot_id = auth_test["user_id"]
        logger.log_info(f"Slack 앱 초기화 성공", {"bot_id": bot_id})
        return app
    except Exception as e:
        logger.log_error("Slack 앱 초기화 중 오류 발생", e)
        raise SlackApiError(f"Slack 앱 초기화 오류: {str(e)}")

def get_bot_id(app: App) -> str:
    """봇 ID를 가져옵니다.

    Args:
        app: Slack 앱 인스턴스

    Returns:
        봇 사용자 ID
    """
    try:
        auth_test = app.client.api_call("auth.test")
        return auth_test["user_id"]
    except SlackApiError as e:
        logger.log_error("봇 ID 조회 중 오류 발생", e)
        raise SlackApiError(f"봇 ID 조회 오류: {str(e)}")

@functools.lru_cache(maxsize=100)
def get_user_info(app: App, user_id: str) -> Dict[str, Any]:
    """사용자 정보를 가져옵니다 (캐싱).

    Args:
        app: Slack 앱 인스턴스
        user_id: Slack 사용자 ID

    Returns:
        사용자 정보 딕셔너리
    """
    # 캐시 확인
    if user_id in _user_info_cache:
        return _user_info_cache[user_id]

    try:
        user_info = app.client.users_info(user=user_id)
        _user_info_cache[user_id] = user_info.get("user", {})
        return _user_info_cache[user_id]
    except SlackApiError as e:
        logger.log_error("사용자 정보 조회 중 오류 발생", e, {"user_id": user_id})
        return {}

def get_user_display_name(app: App, user_id: str) -> str:
    """사용자의 표시 이름을 가져옵니다.

    Args:
        app: Slack 앱 인스턴스
        user_id: Slack 사용자 ID

    Returns:
        사용자 표시 이름
    """
    user_info = get_user_info(app, user_id)
    return user_info.get("profile", {}).get("display_name", "Unknown User")

def send_message(app: App, channel: str, text: str, thread_ts: Optional[str] = None) -> Dict[str, Any]:
    """Slack 채널에 메시지를 보냅니다.

    Args:
        app: Slack 앱 인스턴스
        channel: 채널 ID
        text: 보낼 메시지 텍스트
        thread_ts: 스레드 타임스탬프 (선택 사항)

    Returns:
        Slack API 응답
    """
    try:
        kwargs = {
            "channel": channel,
            "text": text
        }

        if thread_ts:
            kwargs["thread_ts"] = thread_ts

        response = app.client.chat_postMessage(**kwargs)
        return response
    except SlackApiError as e:
        logger.log_error("메시지 전송 중 오류 발생", e, {
            "channel": channel,
            "thread_ts": thread_ts
        })
        raise SlackApiError(f"메시지 전송 오류: {str(e)}")

def update_message(app: App, channel: str, ts: str, text: str) -> Dict[str, Any]:
    """기존 Slack 메시지를 업데이트합니다.

    Args:
        app: Slack 앱 인스턴스
        channel: 채널 ID
        ts: 업데이트할 메시지의 타임스탬프
        text: 새 메시지 텍스트

    Returns:
        Slack API 응답
    """
    try:
        response = app.client.chat_update(
            channel=channel,
            ts=ts,
            text=text
        )
        return response
    except SlackApiError as e:
        logger.log_error("메시지 업데이트 중 오류 발생", e, {
            "channel": channel,
            "ts": ts
        })
        raise SlackApiError(f"메시지 업데이트 오류: {str(e)}")

def delete_message(app: App, channel: str, ts: str) -> Dict[str, Any]:
    """Slack 메시지를 삭제합니다.

    Args:
        app: Slack 앱 인스턴스
        channel: 채널 ID
        ts: 삭제할 메시지의 타임스탬프

    Returns:
        Slack API 응답
    """
    try:
        response = app.client.chat_delete(
            channel=channel,
            ts=ts
        )
        return response
    except SlackApiError as e:
        logger.log_error("메시지 삭제 중 오류 발생", e, {
            "channel": channel,
            "ts": ts
        })
        raise SlackApiError(f"메시지 삭제 오류: {str(e)}")

def upload_file(app: App, channel: str, file_data: bytes, filename: str, thread_ts: Optional[str] = None) -> Dict[str, Any]:
    """Slack 채널에 파일을 업로드합니다.

    Args:
        app: Slack 앱 인스턴스
        channel: 채널 ID
        file_data: 파일 바이너리 데이터
        filename: 파일 이름
        thread_ts: 스레드 타임스탬프 (선택 사항)

    Returns:
        Slack API 응답
    """
    try:
        kwargs = {
            "channel": channel,
            "filename": filename,
            "file": file_data
        }

        if thread_ts:
            kwargs["thread_ts"] = thread_ts

        response = app.client.files_upload_v2(**kwargs)
        return response
    except SlackApiError as e:
        logger.log_error("파일 업로드 중 오류 발생", e, {
            "channel": channel,
            "filename": filename,
            "thread_ts": thread_ts
        })
        raise SlackApiError(f"파일 업로드 오류: {str(e)}")

def get_image_from_slack(image_url: str) -> Optional[bytes]:
    """Slack에서 이미지를 가져옵니다.

    Args:
        image_url: Slack 이미지 URL

    Returns:
        이미지 바이너리 데이터 또는 None
    """
    try:
        headers = {"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"}
        response = requests.get(image_url, headers=headers)

        if response.status_code == 200:
            return response.content
        else:
            logger.log_error(f"이미지 다운로드 실패", None, {
                "url": image_url,
                "status_code": response.status_code
            })
            return None

    except requests.RequestException as e:
        logger.log_error("이미지 다운로드 중 오류 발생", e, {"url": image_url})
        return None

def get_encoded_image_from_slack(image_url: str) -> Optional[str]:
    """Slack에서 이미지를 가져와 base64로 인코딩합니다.

    Args:
        image_url: Slack 이미지 URL

    Returns:
        base64로 인코딩된 이미지 문자열 또는 None
    """
    image = get_image_from_slack(image_url)

    if image:
        return base64.b64encode(image).decode("utf-8")

    return None

def get_thread_messages(app: App, channel: str, thread_ts: str, client_msg_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """스레드 메시지를 가져옵니다.

    Args:
        app: Slack 앱 인스턴스
        channel: 채널 ID
        thread_ts: 스레드 타임스탬프
        client_msg_id: 제외할 메시지의 클라이언트 ID (선택 사항)

    Returns:
        메시지 목록
    """
    try:
        response = app.client.conversations_replies(channel=channel, ts=thread_ts)

        if not response.get("ok"):
            logger.log_error("스레드 메시지 조회 실패", None, {
                "channel": channel,
                "thread_ts": thread_ts,
                "response": response
            })
            return []

        messages = response.get("messages", [])

        # 첫 번째 메시지는 스레드 부모 메시지이므로 제외
        if messages and len(messages) > 0:
            messages = messages[1:]

        # client_msg_id로 메시지 필터링 (있는 경우)
        if client_msg_id:
            messages = [m for m in messages if m.get("client_msg_id") != client_msg_id]

        # 최신 메시지가 먼저 오도록 역순 정렬
        messages.reverse()

        return messages

    except SlackApiError as e:
        logger.log_error("스레드 메시지 조회 중 오류 발생", e, {
            "channel": channel,
            "thread_ts": thread_ts
        })
        return []

def get_reactions(app: App, reactions: List[Dict[str, Any]]) -> str:
    """반응(이모지) 정보를 텍스트로 변환합니다.

    Args:
        app: Slack 앱 인스턴스
        reactions: 반응 목록

    Returns:
        반응 텍스트
    """
    try:
        reaction_map = {}
        reaction_users_cache = {}

        for reaction in reactions:
            reaction_name = ":" + reaction.get("name").split(":")[0] + ":"
            if reaction_name not in reaction_map:
                reaction_map[reaction_name] = []

            reaction_users = reaction.get("users", [])
            for reaction_user in reaction_users:
                if reaction_user not in reaction_users_cache:
                    user_name = get_user_display_name(app, reaction_user)
                    reaction_users_cache[reaction_user] = user_name

                reaction_map[reaction_name].append(reaction_users_cache[reaction_user])

        reaction_texts = []
        for reaction_name, reaction_users in reaction_map.items():
            reaction_texts.append(f"[{settings.KEYWARD_EMOJI} '{reaction_name}' reaction users: {','.join(reaction_users)}]")

        return " ".join(reaction_texts)

    except Exception as e:
        logger.log_error("반응 정보 처리 중 오류 발생", e)
        return ""

def replace_emoji_pattern(text: str) -> str:
    """이모지 패턴을 정리합니다.

    Args:
        text: 원본 텍스트

    Returns:
        정리된 텍스트
    """
    # 패턴: :로 시작하고, 문자 그룹이 있고, :가 오고, 문자 그룹이 있고, :로 끝나는 패턴
    pattern = r":([^:]+):([^:]+):"

    # 첫 번째 그룹만 유지하고 두 번째 그룹은 제거
    replacement = r":\1:"

    # 치환 실행
    result = re.sub(pattern, replacement, text)
    return result

def replace_text(text: str) -> str:
    """텍스트 형식을 변환합니다.

    Args:
        text: 원본 텍스트

    Returns:
        변환된 텍스트
    """
    for old, new in settings.CONVERSION_ARRAY:
        text = text.replace(old, new)
    return text

def parse_slack_event(event: Dict[str, Any], bot_id: str) -> Dict[str, Any]:
    """Slack 이벤트를 파싱합니다.

    Args:
        event: Slack 이벤트 데이터
        bot_id: 봇 사용자 ID

    Returns:
        파싱된 이벤트 정보
    """
    # 스레드 정보 파싱
    thread_ts = event.get("thread_ts", event.get("ts"))

    # 텍스트 정보 파싱
    text = event.get("text", "").strip()

    # 멘션 제거
    text = re.sub(f"<@{bot_id}>", "", text).strip()

    return {
        "thread_ts": thread_ts,
        "text": text,
        "channel": event.get("channel"),
        "user": event.get("user"),
        "client_msg_id": event.get("client_msg_id"),
        "ts": event.get("ts"),
        "has_files": "files" in event
    }

"""
작업 실행 엔진
"""
import time
import requests
from typing import Dict, Any, List

from src.config import settings
from src.api import openai_api, slack_api
from src.api.gemini_api import gemini_api
from src.utils import logger
from .slack_utils import SlackMessageUtils


class TaskExecutor:
    """개별 작업 실행을 담당하는 클래스"""
    
    def __init__(self, app, slack_context: Dict[str, Any]):
        self.app = app
        self.slack_context = slack_context
        self.slack_utils = SlackMessageUtils(app)
    
    def execute_single_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """개별 작업 실행"""
        
        task_type = task['type']
        task_id = task['id']
        
        logger.log_info(f"작업 실행 시작: {task_id}", {"type": task_type})
        
        if task_type == 'text_generation':
            return self._execute_text_generation(task)
        elif task_type == 'image_generation':
            return self._execute_image_generation(task)
        elif task_type == 'image_analysis':
            return self._execute_image_analysis(task)
        elif task_type == 'thread_summary':
            return self._execute_thread_summary(task)
        elif task_type == 'gemini_image_generation':
            return self._execute_gemini_image_generation(task)
        elif task_type == 'gemini_video_generation':
            return self._execute_gemini_video_generation(task)
        elif task_type == 'gemini_text_generation':
            return self._execute_gemini_text_generation(task)
        elif task_type == 'gemini_image_analysis':
            return self._execute_gemini_image_analysis(task)
        else:
            raise ValueError(f"지원하지 않는 작업 타입: {task_type}")
    
    def _execute_text_generation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """텍스트 생성 실행 - 기존 함수 활용"""
        
        # 메시지 준비
        messages = [{"role": "user", "content": task['input']}]
        
        # 스레드 컨텍스트 추가
        if task.get('context'):
            context_messages = []
            for msg in task['context']:
                role = "assistant" if msg.get("bot_id") else "user"
                user_name = msg.get('user_name', 'User')
                content = f"{user_name}: {msg.get('text', '')}"
                context_messages.append({"role": role, "content": content})
            
            # 컨텍스트를 최신 메시지 앞에 삽입
            messages = context_messages + messages
        
        # OpenAI API 호출
        try:
            response = openai_api.generate_chat_completion(
                messages=messages,
                user=self.slack_context.get('user_id', 'unknown'),
                stream=False
            )
            
            content = response.choices[0].message.content
            
            logger.log_info("텍스트 생성 완료", {
                "task_id": task['id'],
                "content_length": len(content)
            })
            
            return {
                'type': 'text',
                'content': content,
                'model': 'gpt-4o'
            }
            
        except Exception as e:
            logger.log_error("텍스트 생성 실패", e, {"task_id": task['id']})
            raise e
    
    def _execute_image_generation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """이미지 생성 실행 - 기존 함수 활용하여 Slack에 바로 업로드"""
        
        try:
            # DALL-E 프롬프트 생성 (한국어 → 영어 변환)
            if self._contains_korean(task['input']):
                prompt_text = f"""
다음 한국어 요청을 DALL-E 이미지 생성을 위한 영어 프롬프트로 변환해주세요:
"{task['input']}"

영어 프롬프트만 반환하세요:
"""
                response = openai_api.generate_chat_completion(
                    messages=[{"role": "user", "content": prompt_text}],
                    user=self.slack_context.get('user_id', 'unknown'),
                    stream=False
                )
                english_prompt = response.choices[0].message.content.strip()
            else:
                english_prompt = task['input']
            
            # DALL-E 이미지 생성
            logger.log_info("DALL-E 이미지 생성 시작", {"prompt": english_prompt[:100]})
            image_result = openai_api.generate_image(english_prompt)
            image_url = image_result["image_url"]
            revised_prompt = image_result["revised_prompt"]
            logger.log_info("DALL-E 이미지 생성 완료", {"image_url_prefix": image_url[:50]})
            
            # DALL-E 이미지 다운로드 (공개 URL이므로 직접 다운로드)
            file_ext = image_url.split(".")[-1].split("?")[0]
            filename = f"{settings.IMAGE_MODEL}.{file_ext}"
            
            logger.log_info("이미지 다운로드 시작", {"url_prefix": image_url[:50], "filename": filename})
            
            # 재시도 로직으로 이미지 다운로드
            
            max_retries = 3
            file_data = None
            
            for attempt in range(max_retries):
                try:
                    response = requests.get(image_url, timeout=30)
                    if response.status_code == 200:
                        file_data = response.content
                        logger.log_info("이미지 다운로드 완료", {
                            "file_size": len(file_data), 
                            "attempt": attempt + 1
                        })
                        break
                    else:
                        raise Exception(f"HTTP {response.status_code}: 이미지 다운로드 실패")
                        
                except Exception as e:
                    logger.log_error(f"이미지 다운로드 시도 {attempt + 1} 실패", e)
                    if attempt == max_retries - 1:
                        raise Exception(f"이미지를 다운로드할 수 없습니다 ({max_retries}회 시도): {str(e)}")
                    time.sleep(2 ** attempt)  # 지수 백오프
            
            if not file_data:
                raise Exception("이미지 다운로드 실패: 데이터가 비어있음")
            
            # Slack에 바로 업로드
            logger.log_info("Slack 파일 업로드 시작", {"filename": filename})
            slack_api.upload_file(
                self.app, 
                self.slack_context["channel"], 
                file_data, 
                filename, 
                self.slack_context.get("thread_ts")
            )
            logger.log_info("Slack 파일 업로드 완료", {"filename": filename})
            
            logger.log_info("이미지 생성 및 업로드 완료", {
                "task_id": task['id'],
                "prompt": english_prompt,
                "revised_prompt": revised_prompt
            })
            
            return {
                'type': 'image',
                'uploaded': True,
                'revised_prompt': revised_prompt,
                'original_prompt': task['input'],
                'filename': filename
            }
            
        except Exception as e:
            logger.log_error("이미지 생성 실패", e, {"task_id": task['id']})
            raise e
    
    def _execute_image_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """이미지 분석 실행 - 기존 함수 활용"""
        
        try:
            # 이미지 정보 추출
            image_info = task.get('uploaded_image')
            if not image_info:
                raise ValueError("분석할 이미지가 제공되지 않았습니다")
            
            # 이미지를 base64로 인코딩
            if 'base64' in image_info:
                # 이미 base64로 인코딩된 경우
                image_base64 = image_info['base64']
            else:
                # URL에서 이미지 다운로드 후 인코딩
                image_base64 = slack_api.get_encoded_image_from_slack(image_info['url'])
            
            if not image_base64:
                raise Exception("이미지 인코딩 실패")
            
            # GPT-4 Vision으로 이미지 분석
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": task['input']},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{image_info.get('mimetype', 'image/png')};base64,{image_base64}"
                        }
                    }
                ]
            }]
            
            response = openai_api.generate_chat_completion(
                messages=messages,
                user=self.slack_context.get('user_id', 'unknown'),
                stream=False
            )
            
            content = response.choices[0].message.content
            
            logger.log_info("이미지 분석 완료", {
                "task_id": task['id'],
                "content_length": len(content)
            })
            
            return {
                'type': 'analysis',
                'content': content,
                'analyzed_image': image_info
            }
            
        except Exception as e:
            logger.log_error("이미지 분석 실패", e, {"task_id": task['id']})
            raise e
    
    def _contains_korean(self, text: str) -> bool:
        """한국어 포함 여부 확인"""
        if not text:
            return False
        
        korean_chars = sum(1 for char in text if '가' <= char <= '힣')
        return korean_chars > len(text) * 0.2  # 20% 이상이 한국어면 한국어로 판단
    
    
    def _execute_thread_summary(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """스레드 요약 실행 - 스레드 내 모든 메시지 요약"""
        
        try:
            # 스레드 정보 확인
            thread_ts = self.slack_context.get("thread_ts")
            if not thread_ts:
                # 스레드가 아닌 경우 단일 메시지 응답
                return {
                    'type': 'text',
                    'content': "현재 스레드가 아니므로 요약할 내용이 없습니다. 스레드 내에서 요약을 요청해주세요.",
                }
            
            # 스레드 메시지 가져오기
            channel = self.slack_context["channel"]
            thread_messages = slack_api.get_thread_messages(
                self.app, 
                channel, 
                thread_ts
            )
            
            if not thread_messages or len(thread_messages) == 0:
                return {
                    'type': 'text', 
                    'content': "요약할 스레드 메시지가 없습니다.",
                }
            
            # 메시지들을 텍스트로 변환
            conversation_text = self._format_thread_messages(thread_messages)
            
            # 요약 프롬프트 생성
            summary_prompt = f"""
다음은 Slack 스레드 대화입니다. 이 대화를 간결하고 명확하게 요약해주세요:

{conversation_text}

요약 요구사항:
1. 주요 주제와 핵심 내용을 포함
2. 중요한 결정사항이나 결론이 있다면 강조
3. 참여자들의 주요 의견이나 관점 반영
4. 3-5개 문단으로 간결하게 정리
5. 한국어로 응답

요약:
"""
            
            # OpenAI API 호출하여 요약 생성
            response = openai_api.generate_chat_completion(
                messages=[{"role": "user", "content": summary_prompt}],
                user=self.slack_context.get('user_id', 'unknown'),
                stream=False
            )
            
            summary_content = response.choices[0].message.content
            
            logger.log_info("스레드 요약 완료", {
                "task_id": task['id'],
                "message_count": len(thread_messages),
                "summary_length": len(summary_content)
            })
            
            return {
                'type': 'text',
                'content': f"📋 **스레드 요약** ({len(thread_messages)}개 메시지)\n\n{summary_content}",
                'message_count': len(thread_messages)
            }
            
        except Exception as e:
            logger.log_error("스레드 요약 실패", e, {"task_id": task['id']})
            raise e
    
    def _format_thread_messages(self, messages: List[Dict[str, Any]]) -> str:
        """스레드 메시지들을 요약하기 쉬운 형태로 포맷팅"""
        
        formatted_messages = []
        
        for i, message in enumerate(messages):
            # 사용자 정보
            user_id = message.get('user', 'unknown')
            
            # 봇 메시지인지 확인
            if message.get('bot_id'):
                user_name = "AI Bot"
            else:
                try:
                    user_name = slack_api.get_user_display_name(self.app, user_id)
                except Exception as e:
                    logger.log_error("사용자 이름 조회 실패", e, {"user_id": user_id})
                    user_name = "User"
            
            # 메시지 텍스트
            text = message.get('text', '').strip()
            if not text:
                continue
                
            # 타임스탬프
            timestamp = message.get('ts', '')
            
            # 메시지 포맷팅
            formatted_messages.append(f"[{i+1}] {user_name}: {text}")
        
        return "\n".join(formatted_messages)
    
    def _execute_gemini_text_generation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Gemini를 사용한 텍스트 생성 실행"""
        
        try:
            # 메시지 준비
            messages = [{"role": "user", "content": task['input']}]
            
            # 스레드 컨텍스트 추가
            if task.get('context'):
                context_messages = []
                for msg in task['context']:
                    role = "assistant" if msg.get("bot_id") else "user"
                    user_name = msg.get('user_name', 'User')
                    content = f"{user_name}: {msg.get('text', '')}"
                    context_messages.append({"role": role, "content": content})
                
                messages = context_messages + messages
            
            # Gemini API 호출
            response = gemini_api.generate_text(
                messages=messages,
                stream=False
            )
            
            content = gemini_api.extract_text_from_response(response)
            
            logger.log_info("Gemini 텍스트 생성 완료", {
                "task_id": task['id'],
                "content_length": len(content)
            })
            
            return {
                'type': 'text',
                'content': content,
                'model': settings.GEMINI_TEXT_MODEL
            }
            
        except Exception as e:
            logger.log_error("Gemini 텍스트 생성 실패", e, {"task_id": task['id']})
            raise e
    
    def _execute_gemini_image_generation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Gemini Imagen을 사용한 이미지 생성 실행"""
        
        try:
            prompt = task['input']
            
            # Gemini Imagen으로 이미지 생성 시도
            response = gemini_api.generate_image(
                prompt=prompt
            )
            
            # 성공한 경우 이미지 처리
            if response.get('images') and len(response['images']) > 0:
                image_data = response['images'][0]
                
                logger.log_info("Gemini 이미지 생성 완료", {
                    "task_id": task['id'],
                    "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt
                })
                
                return {
                    'type': 'image',
                    'image_data': image_data,
                    'prompt': prompt,
                    'model': 'imagen-3.0'
                }
            else:
                raise Exception("생성된 이미지가 없습니다")
                
        except Exception as e:
            logger.log_warning(f"Gemini 이미지 생성 실패, DALL-E로 대체 실행: {str(e)}")
            
            # allowlist 오류이거나 지원되지 않는 경우 DALL-E로 대체
            if "allowlist" in str(e) or "not enabled" in str(e) or "not supported" in str(e):
                logger.log_info("DALL-E 3으로 자동 대체 실행")
                return self._execute_image_generation(task)
            else:
                # 다른 오류는 사용자에게 표시
                return {
                    'type': 'text',
                    'content': f"❌ Gemini 이미지 생성 오류: {str(e)}\n🎨 DALL-E 3으로 다시 시도해보세요.",
                    'model': 'system'
                }
    
    def _execute_gemini_video_generation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Gemini Veo를 사용한 비디오 생성 실행"""
        
        try:
            prompt = task['input']
            duration = task.get('duration', 5)  # 기본 5초
            
            # Gemini Veo로 비디오 생성 시도
            response = gemini_api.generate_video(
                prompt=prompt,
                duration_seconds=duration
            )
            
            # 비디오 생성은 비동기 작업이므로 작업 시작 알림
            logger.log_info("Gemini 비디오 생성 작업 시작", {
                "task_id": task['id'],
                "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt
            })
            
            return {
                'type': 'text',
                'content': f"🎬 Gemini Veo로 비디오 생성을 시작했습니다.\n📝 프롬프트: {prompt}\n⏱️ 예상 소요 시간: 1-3분\n\n{response.get('message', '비디오 생성이 진행 중입니다.')}",
                'model': 'veo-2.0'
            }
                
        except Exception as e:
            logger.log_warning(f"Gemini 비디오 생성 실패: {str(e)}")
            
            # allowlist 오류인 경우 안내
            if "allowlist" in str(e) or "not enabled" in str(e) or "not supported" in str(e):
                return {
                    'type': 'text',
                    'content': "⚠️ Gemini Veo 비디오 생성은 현재 allowlist 뒤에 있어 일반적으로 사용할 수 없습니다.\n🎬 이 기능은 Google에서 승인된 개발자만 사용할 수 있습니다.\n💡 텍스트 생성이나 이미지 생성을 대신 시도해보세요.",
                    'model': 'system'
                }
            else:
                # 다른 오류는 사용자에게 표시
                return {
                    'type': 'text',
                    'content': f"❌ Gemini 비디오 생성 오류: {str(e)}\n💡 텍스트 생성이나 이미지 생성을 대신 시도해보세요.",
                    'model': 'system'
                }
    
    def _execute_gemini_image_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Gemini Vision을 사용한 이미지 분석 실행"""
        
        try:
            # 이미지 정보 추출
            image_info = task.get('uploaded_image')
            if not image_info:
                raise ValueError("분석할 이미지가 제공되지 않았습니다")
            
            # 이미지를 base64로 인코딩
            if 'base64' in image_info:
                image_base64 = image_info['base64']
            else:
                # URL에서 이미지 다운로드 후 인코딩
                image_base64 = slack_api.get_encoded_image_from_slack(image_info['url'])
            
            if not image_base64:
                raise Exception("이미지 인코딩 실패")
            
            # Gemini Vision으로 이미지 분석
            response = gemini_api.analyze_image(
                image_data=image_base64,
                prompt=task['input'],
                mime_type=image_info.get('mimetype', 'image/png')
            )
            
            content = gemini_api.extract_text_from_response(response)
            
            logger.log_info("Gemini 이미지 분석 완료", {
                "task_id": task['id'],
                "content_length": len(content)
            })
            
            return {
                'type': 'analysis',
                'content': content,
                'analyzed_image': image_info,
                'model': settings.GEMINI_TEXT_MODEL
            }
            
        except Exception as e:
            logger.log_error("Gemini 이미지 분석 실패", e, {"task_id": task['id']})
            raise e
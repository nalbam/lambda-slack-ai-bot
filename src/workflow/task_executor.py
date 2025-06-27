"""
작업 실행 엔진
"""
import time
from typing import Dict, Any

from src.api import openai_api, slack_api
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
        """이미지 생성 실행 - 기존 함수 활용"""
        
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
            image_result = openai_api.generate_image(english_prompt)
            
            # 이미지 다운로드
            image_data = slack_api.get_image_from_slack(image_result["image_url"])
            
            if not image_data:
                raise Exception("이미지 다운로드 실패")
            
            logger.log_info("이미지 생성 완료", {
                "task_id": task['id'],
                "prompt": english_prompt,
                "revised_prompt": image_result["revised_prompt"]
            })
            
            return {
                'type': 'image',
                'image_data': image_data,
                'image_url': image_result["image_url"],
                'revised_prompt': image_result["revised_prompt"],
                'original_prompt': task['input']
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
    
    def _check_dependencies(self, task: Dict[str, Any], completed_results: Dict[str, Any]) -> bool:
        """작업 의존성 확인"""
        
        for dep_id in task.get('dependencies', []):
            if dep_id not in completed_results:
                return False
            if completed_results[dep_id]['status'] != 'completed':
                return False
        
        return True
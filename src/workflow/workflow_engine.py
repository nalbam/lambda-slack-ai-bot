"""
4단계 워크플로우 엔진 - 작업 취합 단계 제거
"""
import json
import re
import time
from typing import Dict, Any, List, Optional

from src.api import openai_api, slack_api
from src.utils import logger
from .task_executor import TaskExecutor
from .slack_utils import SlackMessageUtils


class WorkflowEngine:
    """4단계 워크플로우 처리 엔진"""
    
    def __init__(self, app, slack_context: Dict[str, Any]):
        self.app = app
        self.slack_context = slack_context
        self.task_executor = TaskExecutor(app, slack_context)
        self.slack_utils = SlackMessageUtils(app)
    
    def process_user_request(self, user_message: str, context: Dict[str, Any]) -> None:
        """4단계 워크플로우 메인 처리 함수"""
        
        try:
            # 진행 상황 알림
            result = self.slack_context["say"](
                text="🤖 요청을 분석하고 있습니다...", 
                thread_ts=self.slack_context.get("thread_ts")
            )
            latest_ts = result["ts"]
            
            # 1단계: 사용자 의도 파악
            logger.log_info("1단계: 사용자 의도 파악 시작")
            intent_data = self.analyze_user_intent(user_message, context)
            
            # 2단계: 작업 나열  
            logger.log_info("2단계: 작업 나열 시작")
            task_list = self.create_task_list(intent_data, context)
            
            # 진행 상황 업데이트 및 예상 시간 안내
            estimated_time = intent_data.get('estimated_time', '알 수 없음')
            self.update_progress(latest_ts, f"📋 {len(task_list)}개 작업을 처리합니다... (예상 시간: {estimated_time}초)")
            
            # 3단계: 작업 처리 및 즉시 회신
            logger.log_info("3단계: 작업 처리 및 회신 시작")
            self.execute_and_respond_tasks(task_list, latest_ts)
            
            logger.log_info("워크플로우 처리 완료", {
                "total_tasks": len(task_list)
            })
            
        except Exception as e:
            logger.log_error("워크플로우 처리 실패", e)
            self.handle_workflow_error(e, user_message, context)
    
    def analyze_user_intent(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """1단계: OpenAI를 통한 사용자 의도 파악"""
        
        capabilities = self.load_bot_capabilities()
        
        prompt = f"""
사용자 메시지: "{user_message}"

대화 컨텍스트:
- 사용자: {context.get('user_name', 'Unknown')}
- 스레드 길이: {context.get('thread_length', 0)}개 메시지
- 첨부 이미지: {'있음' if context.get('uploaded_image') else '없음'}

봇의 능력: {capabilities}

사용자 메시지를 분석하여 필요한 작업들을 JSON으로 응답해주세요:

{{
    "user_intent": "사용자 의도 요약",
    "required_tasks": [
        {{
            "task_id": "unique_id",
            "task_type": "text_generation|image_generation|image_analysis|thread_summary",
            "description": "작업 설명",
            "input_data": "작업 입력",
            "priority": 1-10,
            "depends_on": []
        }}
    ],
    "execution_strategy": "sequential|parallel",
    "estimated_time": "예상시간(초)"
}}

예시:
- "파이썬 설명해줘" → text_generation 작업 1개
- "고양이 그려줘" → image_generation 작업 1개  
- "AI 설명하고 로봇 이미지도 그려줘" → text_generation + image_generation 작업 2개
- "스레드 요약해줘" → thread_summary 작업 1개

JSON만 응답하세요.
"""
        
        try:
            response = openai_api.generate_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                user=context.get('user_id', 'unknown'),
                stream=False,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            try:
                return self.parse_intent_response(content)
            except (json.JSONDecodeError, ValueError) as e:
                logger.log_error("의도 분석 파싱 실패, fallback 사용", e, {"content": content[:200]})
                return self.create_fallback_intent(user_message, context)
            
        except Exception as e:
            logger.log_error("의도 분석 실패", e)
            return self.create_fallback_intent(user_message, context)
    
    def parse_intent_response(self, response_content: str) -> Dict[str, Any]:
        """OpenAI 응답에서 JSON 추출 및 파싱"""
        
        try:
            # JSON 코드 블록 제거
            content = re.sub(r'```json\n|```\n|```', '', response_content)
            content = content.strip()
            
            # JSON 파싱
            result = json.loads(content)
            
            # 필수 필드 검증
            required_fields = ['user_intent', 'required_tasks']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"필수 필드 누락: {field}")
            
            # 작업 필드 검증
            for task in result['required_tasks']:
                required_task_fields = ['task_id', 'task_type', 'description']
                for field in required_task_fields:
                    if field not in task:
                        raise ValueError(f"작업 필수 필드 누락: {field}")
            
            logger.log_info("의도 분석 성공", {
                "intent": result['user_intent'],
                "task_count": len(result['required_tasks'])
            })
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.log_error("의도 분석 파싱 실패", e, {"content": response_content[:200]})
            raise e
    
    def create_fallback_intent(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """파싱 실패 시 기본 의도 분석"""
        
        logger.log_info("Fallback 의도 분석 사용")
        
        # 키워드 기반 간단한 분석
        if context.get('uploaded_image'):
            return {
                "user_intent": "이미지 분석 요청",
                "required_tasks": [{
                    "task_id": "fallback_image_analysis",
                    "task_type": "image_analysis", 
                    "description": "업로드된 이미지 분석",
                    "input_data": user_message,
                    "priority": 1,
                    "depends_on": []
                }],
                "execution_strategy": "sequential",
                "estimated_time": "10"
            }
        elif any(keyword in user_message for keyword in ["요약", "summarize", "summary"]):
            return {
                "user_intent": "스레드 요약 요청",
                "required_tasks": [{
                    "task_id": "fallback_thread_summary",
                    "task_type": "thread_summary",
                    "description": "스레드 메시지 요약",
                    "input_data": user_message,
                    "priority": 1,
                    "depends_on": []
                }],
                "execution_strategy": "sequential",
                "estimated_time": "8"
            }
        elif any(keyword in user_message for keyword in ["그려", "그림", "이미지", "생성"]):
            return {
                "user_intent": "이미지 생성 요청",
                "required_tasks": [{
                    "task_id": "fallback_image_gen",
                    "task_type": "image_generation",
                    "description": "이미지 생성",
                    "input_data": user_message,
                    "priority": 1,
                    "depends_on": []
                }],
                "execution_strategy": "sequential",
                "estimated_time": "15"
            }
        else:
            return {
                "user_intent": "텍스트 응답 요청",
                "required_tasks": [{
                    "task_id": "fallback_text",
                    "task_type": "text_generation",
                    "description": "텍스트 응답 생성",
                    "input_data": user_message,
                    "priority": 1,
                    "depends_on": []
                }],
                "execution_strategy": "sequential",
                "estimated_time": "8"
            }
    
    def create_task_list(self, intent_data: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """2단계: 의도를 실행 가능한 작업 목록으로 변환"""
        
        tasks = []
        
        for task_info in intent_data['required_tasks']:
            task = {
                'id': task_info['task_id'],
                'type': task_info['task_type'],
                'description': task_info['description'],
                'input': task_info.get('input_data', ''),
                'priority': task_info.get('priority', 5),
                'dependencies': task_info.get('depends_on', []),
                'status': 'pending',
                'result': None,
                'error': None,
                'execution_time': None
            }
            
            # 컨텍스트 정보 추가
            if context.get('thread_messages'):
                task['context'] = context['thread_messages']
            if context.get('uploaded_image'):
                task['uploaded_image'] = context['uploaded_image']
            
            tasks.append(task)
        
        # 우선순위와 의존성에 따라 정렬
        return self.sort_tasks_by_dependency(tasks)
    
    def sort_tasks_by_dependency(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """의존성을 고려하여 작업 순서 정렬"""
        
        sorted_tasks = []
        remaining_tasks = tasks.copy()
        max_iterations = len(tasks) * 2  # 무한 루프 방지
        iteration = 0
        
        while remaining_tasks and iteration < max_iterations:
            iteration += 1
            initial_count = len(remaining_tasks)
            
            # 의존성이 없거나 이미 완료된 작업들 찾기
            ready_tasks = []
            for task in remaining_tasks:
                dependencies_met = all(
                    dep_id in [t['id'] for t in sorted_tasks] 
                    for dep_id in task['dependencies']
                )
                if dependencies_met:
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # 순환 의존성 감지 - 우선순위가 가장 높은 작업 선택
                logger.log_warning("순환 의존성 감지됨, 우선순위 기준으로 작업 선택", {
                    "remaining_tasks": [t['id'] for t in remaining_tasks]
                })
                ready_tasks = sorted(remaining_tasks, key=lambda x: x['priority'])[:1]
            
            # 우선순위가 높은 순으로 정렬
            ready_tasks.sort(key=lambda x: x['priority'])
            
            for task in ready_tasks:
                sorted_tasks.append(task)
                remaining_tasks.remove(task)
            
            # 진행이 없으면 무한 루프 방지
            if len(remaining_tasks) == initial_count:
                logger.log_error("작업 정렬 중 진행 없음, 강제 종료", None, {
                    "remaining_tasks": [t['id'] for t in remaining_tasks]
                })
                break
        
        # 남은 작업들 우선순위로 추가
        if remaining_tasks:
            logger.log_warning("정렬되지 않은 작업들 우선순위로 추가", {
                "remaining_count": len(remaining_tasks)
            })
            remaining_tasks.sort(key=lambda x: x['priority'])
            sorted_tasks.extend(remaining_tasks)
        
        return sorted_tasks
    
    def execute_and_respond_tasks(self, task_list: List[Dict[str, Any]], progress_ts: str) -> None:
        """3단계: 작업들을 순차적으로 실행하고 즉시 회신"""
        
        for i, task in enumerate(task_list):
            try:
                # 진행 상황 업데이트
                progress = f"⚙️ 작업 {i+1}/{len(task_list)}: {task['description']} 처리 중..."
                self.update_progress(progress_ts, progress)
                
                # 작업 실행
                start_time = time.time()
                result = self.task_executor.execute_single_task(task)
                execution_time = time.time() - start_time
                
                # 즉시 결과 회신
                self._send_task_result(result, task, progress_ts)
                
                logger.log_info(f"작업 {task['id']} 완료 및 회신", {
                    "type": task['type'],
                    "time": execution_time
                })
                
            except Exception as e:
                logger.log_error(f"작업 {task['id']} 실패", e)
                # 에러 메시지 즉시 전송
                self.update_progress(progress_ts, f"❌ {task['description']} 처리 중 오류 발생: {str(e)}")
        
        # 모든 작업 완료 메시지
        self.update_progress(progress_ts, "✅ 모든 작업이 완료되었습니다.")
    
    def _send_task_result(self, result: Dict[str, Any], task: Dict[str, Any], progress_ts: str) -> None:
        """작업 결과를 즉시 Slack에 새로운 메시지로 전송"""
        
        try:
            if result['type'] == 'text':
                # 텍스트 결과를 새로운 메시지로 스트리밍 전송
                response = self.slack_context["say"](
                    text="💭 응답 생성 중...", 
                    thread_ts=self.slack_context.get("thread_ts")
                )
                new_message_ts = response["ts"]
                
                messages = [{"role": "assistant", "content": result['content']}]
                self.slack_utils.reply_text_stream(
                    messages=messages,
                    say=self.slack_context["say"],
                    channel=self.slack_context["channel"],
                    thread_ts=self.slack_context.get("thread_ts"),
                    latest_ts=new_message_ts,  # 새로운 메시지 사용
                    user=self.slack_context.get("user_id", "unknown")
                )
                
            elif result['type'] == 'image':
                # 이미지는 이미 TaskExecutor에서 업로드됨
                # 별도 프롬프트 메시지를 새로 전송
                if result.get('revised_prompt'):
                    self.slack_context["say"](
                        text=f"🎨 {result['revised_prompt']}", 
                        thread_ts=self.slack_context.get("thread_ts")
                    )
                
            elif result['type'] == 'analysis':
                # 분석 결과를 새로운 메시지로 스트리밍 전송
                response = self.slack_context["say"](
                    text="🔍 분석 결과 전송 중...", 
                    thread_ts=self.slack_context.get("thread_ts")
                )
                new_message_ts = response["ts"]
                
                messages = [{"role": "assistant", "content": result['content']}]
                self.slack_utils.reply_text_stream(
                    messages=messages,
                    say=self.slack_context["say"],
                    channel=self.slack_context["channel"],
                    thread_ts=self.slack_context.get("thread_ts"),
                    latest_ts=new_message_ts,  # 새로운 메시지 사용
                    user=self.slack_context.get("user_id", "unknown")
                )
                
        except Exception as e:
            logger.log_error("작업 결과 전송 실패", e)
            # 오류도 새로운 메시지로 전송
            self.slack_context["say"](
                text=f"❌ 작업 결과 전송 중 오류 발생: {str(e)}", 
                thread_ts=self.slack_context.get("thread_ts")
            )
    
    
    def update_progress(self, message_ts: str, text: str) -> None:
        """진행 상황 업데이트"""
        
        try:
            slack_api.update_message(
                self.app,
                self.slack_context["channel"],
                message_ts,
                text
            )
        except Exception as e:
            logger.log_error("진행 상황 업데이트 실패", e)
    
    def load_bot_capabilities(self) -> str:
        """봇 능력 목록 로드"""
        
        return """
1. 텍스트 생성 및 대화
   - 질문 답변, 설명, 요약
   - 번역 (한국어 ↔ 영어)  
   - 코드 생성 및 설명
   - 창작 글쓰기 (시, 에세이, 이야기)
   - 문서 작성 (보고서, 계획서)

2. 이미지 생성
   - DALL-E를 통한 다양한 스타일의 이미지 생성
   - 로고, 일러스트, 개념 시각화

3. 이미지 분석  
   - 이미지 내용 설명
   - 차트, 그래프 분석
   - 코드 스크린샷 해석
   - 문서 이미지 읽기

4. 스레드 요약
   - 스레드 내 모든 메시지 분석 및 요약
   - 주요 주제 및 결론 추출
   - 참여자별 의견 정리
"""
    
    def handle_workflow_error(self, error: Exception, user_message: str, context: Dict[str, Any]) -> None:
        """워크플로우 실패 시 간단한 에러 처리"""
        
        logger.log_error("워크플로우 실패", error, {
            "user_message": user_message[:100],
            "user_id": context.get("user_id"),
            "has_image": bool(context.get("uploaded_image"))
        })
        
        # 간단한 에러 메시지 전송
        try:
            self.slack_context["say"](
                text="⚠️ 죄송합니다. 요청을 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
                thread_ts=self.slack_context.get("thread_ts")
            )
        except Exception as send_error:
            logger.log_error("에러 메시지 전송도 실패", send_error)
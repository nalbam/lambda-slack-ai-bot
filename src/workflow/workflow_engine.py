"""
5단계 워크플로우 엔진
"""
import json
import re
import time
from typing import Dict, Any, List, Optional

from src.api import openai_api, slack_api
from src.utils import logger
from .task_executor import TaskExecutor


class WorkflowEngine:
    """5단계 워크플로우 처리 엔진"""
    
    def __init__(self, app, slack_context: Dict[str, Any]):
        self.app = app
        self.slack_context = slack_context
        self.task_executor = TaskExecutor(app, slack_context)
    
    def process_user_request(self, user_message: str, context: Dict[str, Any]) -> None:
        """5단계 워크플로우 메인 처리 함수"""
        
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
            
            # 진행 상황 업데이트
            self.update_progress(latest_ts, f"📋 {len(task_list)}개 작업을 처리합니다...")
            
            # 3단계: 작업 처리
            logger.log_info("3단계: 작업 처리 시작")
            task_results = self.execute_tasks(task_list, latest_ts)
            
            # 4단계: 작업 취합
            logger.log_info("4단계: 작업 취합 시작")
            aggregated_results = self.aggregate_results(task_results, intent_data)
            
            # 5단계: 회신
            logger.log_info("5단계: 최종 회신 시작")
            self.send_final_response(aggregated_results, latest_ts)
            
            logger.log_info("워크플로우 처리 완료", {
                "total_tasks": len(task_list),
                "successful": aggregated_results['summary']['successful'],
                "failed": aggregated_results['summary']['failed']
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
            "task_type": "text_generation|image_generation|image_analysis",
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
            return self.parse_intent_response(content)
            
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
        
        while remaining_tasks:
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
                # 순환 의존성이 있는 경우 우선순위로 정렬
                ready_tasks = sorted(remaining_tasks, key=lambda x: x['priority'])[:1]
            
            # 우선순위가 높은 순으로 정렬
            ready_tasks.sort(key=lambda x: x['priority'])
            
            for task in ready_tasks:
                sorted_tasks.append(task)
                remaining_tasks.remove(task)
        
        return sorted_tasks
    
    def execute_tasks(self, task_list: List[Dict[str, Any]], progress_ts: str) -> Dict[str, Any]:
        """3단계: 작업들을 순차적으로 실행"""
        
        results = {}
        
        for i, task in enumerate(task_list):
            try:
                # 진행 상황 업데이트
                progress = f"⚙️ 작업 {i+1}/{len(task_list)}: {task['description']} 처리 중..."
                self.update_progress(progress_ts, progress)
                
                # 작업 실행
                task['status'] = 'running'
                start_time = time.time()
                
                result = self.task_executor.execute_single_task(task)
                
                task['status'] = 'completed'
                task['result'] = result
                task['execution_time'] = time.time() - start_time
                results[task['id']] = task
                
                logger.log_info(f"작업 {task['id']} 완료", {
                    "type": task['type'],
                    "time": task['execution_time']
                })
                
            except Exception as e:
                task['status'] = 'failed'
                task['error'] = str(e)
                task['execution_time'] = time.time() - start_time if 'start_time' in locals() else 0
                results[task['id']] = task
                logger.log_error(f"작업 {task['id']} 실패", e)
        
        return results
    
    def aggregate_results(self, task_results: Dict[str, Any], intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """4단계: 작업 결과들을 통합"""
        
        successful_tasks = {k: v for k, v in task_results.items() if v['status'] == 'completed'}
        failed_tasks = {k: v for k, v in task_results.items() if v['status'] == 'failed'}
        
        # 결과 타입별 분류
        text_results = []
        image_results = []
        analysis_results = []
        
        for task_id, task in successful_tasks.items():
            if not task.get('result'):
                continue
                
            result = task['result']
            
            if result['type'] == 'text':
                text_results.append({
                    'content': result['content'],
                    'description': task['description']
                })
            elif result['type'] == 'image':
                image_results.append({
                    'image_data': result['image_data'],
                    'prompt': result['revised_prompt'],
                    'description': task['description']
                })
            elif result['type'] == 'analysis':
                analysis_results.append({
                    'content': result['content'],
                    'description': task['description']
                })
        
        return {
            'original_intent': intent_data['user_intent'],
            'results': {
                'text_content': text_results,
                'images': image_results,
                'analyses': analysis_results
            },
            'summary': {
                'total_tasks': len(task_results),
                'successful': len(successful_tasks),
                'failed': len(failed_tasks)
            },
            'errors': [{'description': task['description'], 'error': task['error']} 
                      for task in failed_tasks.values()]
        }
    
    def send_final_response(self, aggregated_results: Dict[str, Any], message_ts: str) -> None:
        """5단계: 최종 응답 생성 및 전송"""
        
        try:
            # OpenAI에게 결과 정리 요청
            summary_prompt = self.create_response_summary_prompt(aggregated_results)
            
            response = openai_api.generate_chat_completion(
                messages=[{"role": "user", "content": summary_prompt}],
                user="response_generator",
                stream=False
            )
            
            final_text = response.choices[0].message.content
            
        except Exception as e:
            logger.log_error("응답 포맷팅 실패", e)
            # Fallback 응답
            final_text = self.create_simple_summary(aggregated_results)
        
        # Slack에 텍스트 응답 전송
        slack_api.update_message(
            self.app, 
            self.slack_context["channel"], 
            message_ts, 
            final_text
        )
        
        # 이미지들 업로드
        for i, image in enumerate(aggregated_results['results']['images']):
            try:
                slack_api.upload_file(
                    self.app,
                    self.slack_context["channel"],
                    image['image_data'],
                    f"generated_{i+1}.png",
                    self.slack_context.get("thread_ts")
                )
            except Exception as e:
                logger.log_error(f"이미지 {i+1} 업로드 실패", e)
    
    def create_response_summary_prompt(self, results: Dict[str, Any]) -> str:
        """응답 정리를 위한 프롬프트 생성"""
        
        text_content = results['results']['text_content']
        images = results['results']['images']
        analyses = results['results']['analyses']
        errors = results['errors']
        
        prompt = f"""
다음은 사용자 요청 "{results['original_intent']}"에 대한 처리 결과입니다:

텍스트 결과:
{chr(10).join([f"- {item['description']}: {item['content'][:300]}..." for item in text_content])}

이미지 결과:
{chr(10).join([f"- {item['description']}: 이미지 생성됨 (프롬프트: {item['prompt']})" for item in images])}

분석 결과:
{chr(10).join([f"- {item['description']}: {item['content'][:300]}..." for item in analyses])}

오류:
{chr(10).join([f"- {error['description']}: {error['error']}" for error in errors]) if errors else "없음"}

이 결과들을 사용자에게 친근하고 이해하기 쉽게 정리해서 하나의 통합된 응답으로 만들어주세요.
이미지가 생성되었다면 "이미지를 생성했습니다"라고 언급하고, 별도로 업로드된다고 설명하세요.
오류가 있다면 자연스럽게 언급하되 과도하게 강조하지 마세요.
"""
        
        return prompt
    
    def create_simple_summary(self, results: Dict[str, Any]) -> str:
        """간단한 응답 요약 (fallback)"""
        
        parts = []
        
        # 텍스트 결과
        for item in results['results']['text_content']:
            parts.append(item['content'])
        
        # 이미지 결과
        if results['results']['images']:
            parts.append(f"{len(results['results']['images'])}개의 이미지를 생성했습니다.")
        
        # 분석 결과  
        for item in results['results']['analyses']:
            parts.append(item['content'])
        
        # 오류 언급
        if results['errors']:
            parts.append(f"일부 작업에서 오류가 발생했습니다: {len(results['errors'])}개 작업 실패")
        
        return "\n\n".join(parts) if parts else "요청을 처리했지만 결과를 생성할 수 없었습니다."
    
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
"""
    
    def handle_workflow_error(self, error: Exception, user_message: str, context: Dict[str, Any]) -> None:
        """워크플로우 실패 시 기존 방식으로 fallback"""
        
        logger.log_error("워크플로우 실패, fallback 사용", error)
        
        try:
            # 기존 MessageHandler 방식으로 처리
            from src.handlers.message_handler import MessageHandler
            
            handler = MessageHandler(self.app)
            
            # 간단한 키워드 기반 분류
            if context.get('uploaded_image'):
                # 이미지 분석
                content = [{
                    "type": "text", 
                    "text": f"{context['user_name']}: {user_message}"
                }, {
                    "type": "image_url",
                    "image_url": {"url": f"data:{context['uploaded_image']['mimetype']};base64,{context['uploaded_image']['base64']}"}
                }]
                handler.conversation(
                    self.slack_context["say"],
                    self.slack_context.get("thread_ts"),
                    content,
                    self.slack_context["channel"],
                    context.get("user_id"),
                    context.get("client_msg_id"),
                    "text"
                )
            elif any(keyword in user_message for keyword in ["그려", "그림", "이미지", "생성"]):
                # 이미지 생성
                content = [{"type": "text", "text": f"{context['user_name']}: {user_message}"}]
                handler.image_generate(
                    self.slack_context["say"],
                    self.slack_context.get("thread_ts"),
                    content,
                    self.slack_context["channel"],
                    context.get("client_msg_id"),
                    "image"
                )
            else:
                # 일반 대화
                content = [{"type": "text", "text": f"{context['user_name']}: {user_message}"}]
                handler.conversation(
                    self.slack_context["say"],
                    self.slack_context.get("thread_ts"),
                    content,
                    self.slack_context["channel"],
                    context.get("user_id"),
                    context.get("client_msg_id"),
                    "text"
                )
                
        except Exception as fallback_error:
            logger.log_error("Fallback도 실패", fallback_error)
            
            # 최후 수단: 간단한 에러 메시지
            try:
                self.slack_context["say"](
                    text="죄송합니다. 요청을 처리하는 중 오류가 발생했습니다. 다시 시도해 주세요.",
                    thread_ts=self.slack_context.get("thread_ts")
                )
            except:
                pass  # 에러 메시지도 보낼 수 없는 경우
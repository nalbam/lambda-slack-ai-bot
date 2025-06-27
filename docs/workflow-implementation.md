# 5단계 워크플로우 구현 가이드

## 전체 워크플로우 개요

```
사용자 입력
    ↓
1. 사용자 의도 파악 (OpenAI 분석)
    ↓  
2. 작업 나열 (JSON → 실행 가능한 작업들)
    ↓
3. 작업 처리 (기존 함수들 활용)
    ↓
4. 작업 취합 (결과 통합)
    ↓
5. 회신 (OpenAI 정리 + Slack 전송)
```

## 메인 워크플로우 엔진

### WorkflowEngine 클래스

```python
# src/workflow/workflow_engine.py
import time
from typing import Dict, Any, List

class WorkflowEngine:
    def __init__(self, app, slack_context):
        self.app = app
        self.slack_context = slack_context
        self.task_executor = TaskExecutor(app, slack_context)
    
    def process_user_request(self, user_message: str, context: dict) -> None:
        \"\"\"5단계 워크플로우 메인 처리 함수\"\"\"
        
        try:
            # 진행 상황 알림
            result = self.slack_context["say"](
                text="🤖 요청을 분석하고 있습니다...", 
                thread_ts=self.slack_context.get("thread_ts")
            )
            latest_ts = result["ts"]
            
            # 1단계: 사용자 의도 파악
            intent_data = self.analyze_user_intent(user_message, context)
            
            # 2단계: 작업 나열  
            task_list = self.create_task_list(intent_data, context)
            
            # 진행 상황 업데이트
            self.update_progress(latest_ts, f"📋 {len(task_list)}개 작업을 처리합니다...")
            
            # 3단계: 작업 처리
            task_results = self.execute_tasks(task_list, latest_ts)
            
            # 4단계: 작업 취합
            aggregated_results = self.aggregate_results(task_results, intent_data)
            
            # 5단계: 회신
            self.send_final_response(aggregated_results, latest_ts)
            
        except Exception as e:
            logger.log_error("Workflow processing failed", e)
            self.handle_workflow_error(e, user_message, context)
    
    def analyze_user_intent(self, user_message: str, context: dict) -> dict:
        \"\"\"1단계: OpenAI를 통한 사용자 의도 파악\"\"\"
        
        # bot-capabilities.md의 능력 목록 로드
        capabilities = self.load_bot_capabilities()
        
        prompt = f\"\"\"
사용자 메시지: "{user_message}"

봇의 능력: {capabilities}

사용자 메시지를 분석하여 필요한 작업들을 JSON으로 응답:
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
\"\"\"
        
        try:
            response = openai_api.generate_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                user=context.get('user_id', 'unknown'),
                stream=False,
                temperature=0.1
            )
            
            return self.parse_intent_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.log_error("Intent analysis failed", e)
            return self.create_fallback_intent(user_message)
    
    def create_task_list(self, intent_data: dict, context: dict) -> List[dict]:
        \"\"\"2단계: 의도를 실행 가능한 작업 목록으로 변환\"\"\"
        
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
                'error': None
            }
            
            # 컨텍스트 정보 추가
            if context.get('thread_messages'):
                task['context'] = context['thread_messages']
            if context.get('uploaded_image'):
                task['uploaded_image'] = context['uploaded_image']
            
            tasks.append(task)
        
        return self.sort_tasks_by_dependency(tasks)
    
    def execute_tasks(self, task_list: List[dict], progress_ts: str) -> dict:
        \"\"\"3단계: 작업들을 순차적으로 실행\"\"\"
        
        results = {}
        
        for i, task in enumerate(task_list):
            try:
                # 진행 상황 업데이트
                progress = f"⚙️ 작업 {i+1}/{len(task_list)}: {task['description']} 처리 중..."
                self.update_progress(progress_ts, progress)
                
                # 작업 실행
                task['status'] = 'running'
                result = self.task_executor.execute_single_task(task)
                
                task['status'] = 'completed'
                task['result'] = result
                results[task['id']] = task
                
            except Exception as e:
                task['status'] = 'failed'
                task['error'] = str(e)
                results[task['id']] = task
                logger.log_error(f"Task {task['id']} failed", e)
        
        return results
    
    def aggregate_results(self, task_results: dict, intent_data: dict) -> dict:
        \"\"\"4단계: 작업 결과들을 통합\"\"\"
        
        successful_tasks = {k: v for k, v in task_results.items() if v['status'] == 'completed'}
        failed_tasks = {k: v for k, v in task_results.items() if v['status'] == 'failed'}
        
        # 결과 타입별 분류
        text_results = []
        image_results = []
        analysis_results = []
        
        for task_id, task in successful_tasks.items():
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
    
    def send_final_response(self, aggregated_results: dict, message_ts: str) -> None:
        \"\"\"5단계: 최종 응답 생성 및 전송\"\"\"
        
        try:
            # OpenAI에게 결과 정리 요청
            summary_prompt = f\"\"\"
다음 작업 결과들을 사용자에게 친근하게 정리해주세요:

원래 요청: {aggregated_results['original_intent']}

텍스트 결과:
{chr(10).join([f"- {item['content']}" for item in aggregated_results['results']['text_content']])}

이미지 결과: {len(aggregated_results['results']['images'])}개 생성됨

분석 결과:
{chr(10).join([f"- {item['content']}" for item in aggregated_results['results']['analyses']])}

하나의 통합된 응답으로 정리해주세요. 이미지는 별도로 업로드됩니다.
\"\"\"
            
            response = openai_api.generate_chat_completion(
                messages=[{"role": "user", "content": summary_prompt}],
                user="response_generator",
                stream=False
            )
            
            final_text = response.choices[0].message.content
            
        except Exception as e:
            logger.log_error("Response formatting failed", e)
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
            slack_api.upload_file(
                self.app,
                self.slack_context["channel"],
                image['image_data'],
                f"generated_{i+1}.png",
                self.slack_context.get("thread_ts")
            )
    
    def handle_workflow_error(self, error: Exception, user_message: str, context: dict):
        \"\"\"워크플로우 실패 시 기존 방식으로 fallback\"\"\"
        
        logger.log_error("Workflow failed, using fallback", error)
        
        # 기존 MessageHandler 방식으로 처리
        from src.handlers.message_handler import MessageHandler
        
        handler = MessageHandler(self.app)
        
        # 키워드 기반 간단 분류
        if "그려" in user_message or "이미지" in user_message:
            content = [{"type": "text", "text": user_message}]
            handler.image_generate(
                self.slack_context["say"],
                self.slack_context.get("thread_ts"),
                content,
                self.slack_context["channel"],
                context.get("client_msg_id"),
                "image"
            )
        else:
            content = [{"type": "text", "text": user_message}]
            handler.conversation(
                self.slack_context["say"],
                self.slack_context.get("thread_ts"), 
                content,
                self.slack_context["channel"],
                context.get("user_id"),
                context.get("client_msg_id"),
                "text"
            )
```

## 기존 MessageHandler 통합

### 기존 핸들러 수정

```python
# src/handlers/message_handler.py에 추가

def handle_mention(self, body: Dict[str, Any], say: Say) -> None:
    \"\"\"앱 멘션 이벤트 핸들러 - 워크플로우 엔진 통합\"\"\"
    
    event = body.get("event", {})
    parsed_event = slack_api.parse_slack_event(event, self.bot_id)
    
    try:
        # 워크플로우 엔진 사용 여부 결정
        if self.should_use_workflow(parsed_event["text"]):
            
            # 컨텍스트 준비
            context = {
                'user_id': parsed_event["user"],
                'user_name': slack_api.get_user_display_name(self.app, parsed_event["user"]),
                'thread_messages': self.get_thread_context(parsed_event),
                'uploaded_image': self.extract_uploaded_image(event),
                'client_msg_id': parsed_event["client_msg_id"]
            }
            
            # Slack 컨텍스트 준비
            slack_context = {
                'app': self.app,
                'say': say,
                'channel': parsed_event["channel"],
                'thread_ts': parsed_event["thread_ts"]
            }
            
            # 워크플로우 엔진으로 처리
            from src.workflow.workflow_engine import WorkflowEngine
            engine = WorkflowEngine(self.app, slack_context)
            engine.process_user_request(parsed_event["text"], context)
            
        else:
            # 기존 방식으로 처리
            self.handle_with_existing_method(body, say)
            
    except Exception as e:
        logger.log_error("Enhanced handler failed, using fallback", e)
        self.handle_with_existing_method(body, say)

def should_use_workflow(self, text: str) -> bool:
    \"\"\"워크플로우 엔진 사용 여부 결정\"\"\"
    
    # 복합 요청 키워드 감지
    image_keywords = ["그려", "그림", "이미지", "생성", "만들어"]
    text_keywords = ["설명", "요약", "분석", "작성", "알려"]
    
    has_image_request = any(word in text for word in image_keywords)
    has_text_request = any(word in text for word in text_keywords)
    
    # 복합 요청이거나 복잡한 요청인 경우 워크플로우 사용
    return (has_image_request and has_text_request) or len(text.split()) > 10

def handle_with_existing_method(self, body: Dict[str, Any], say: Say) -> None:
    \"\"\"기존 방식으로 처리 (fallback)\"\"\"
    
    event = body.get("event", {})
    parsed_event = slack_api.parse_slack_event(event, self.bot_id)
    
    content, content_type = self.content_from_message(
        parsed_event["text"], event, parsed_event["user"]
    )
    
    if content_type == "image":
        self.image_generate(say, parsed_event["thread_ts"], content, 
                          parsed_event["channel"], parsed_event["client_msg_id"], content_type)
    else:
        self.conversation(say, parsed_event["thread_ts"], content, 
                        parsed_event["channel"], parsed_event["user"], 
                        parsed_event["client_msg_id"], content_type)
```

## TaskExecutor 구현

```python
# src/workflow/task_executor.py
import time
from typing import Dict, Any

class TaskExecutor:
    def __init__(self, app, context):
        self.app = app
        self.context = context
    
    def execute_single_task(self, task: dict) -> dict:
        \"\"\"개별 작업 실행\"\"\"
        
        task_type = task['type']
        
        if task_type == 'text_generation':
            return self._execute_text_generation(task)
        elif task_type == 'image_generation':
            return self._execute_image_generation(task)
        elif task_type == 'image_analysis':
            return self._execute_image_analysis(task)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    
    def _execute_text_generation(self, task: dict) -> dict:
        \"\"\"텍스트 생성 실행 - 기존 함수 활용\"\"\"
        
        messages = [{"role": "user", "content": task['input']}]
        
        # 스레드 컨텍스트 추가
        if task.get('context'):
            for msg in task['context']:
                role = "assistant" if msg.get("bot_id") else "user"
                messages.insert(-1, {"role": role, "content": msg.get('text', '')})
        
        response = openai_api.generate_chat_completion(
            messages=messages,
            user=self.context.get('user_id', 'unknown'),
            stream=False
        )
        
        return {
            'type': 'text',
            'content': response.choices[0].message.content
        }
    
    def _execute_image_generation(self, task: dict) -> dict:
        \"\"\"이미지 생성 실행 - 기존 함수 활용\"\"\"
        
        # DALL-E 프롬프트 생성 (한국어 → 영어 변환)
        if self._contains_korean(task['input']):
            prompt_text = f"다음을 영어 이미지 프롬프트로 변환: {task['input']}"
            response = openai_api.generate_chat_completion(
                messages=[{"role": "user", "content": prompt_text}],
                user=self.context.get('user_id', 'unknown'),
                stream=False
            )
            english_prompt = response.choices[0].message.content.strip()
        else:
            english_prompt = task['input']
        
        # 이미지 생성
        image_result = openai_api.generate_image(english_prompt)
        image_data = slack_api.get_image_from_slack(image_result["image_url"])
        
        return {
            'type': 'image',
            'image_data': image_data,
            'revised_prompt': image_result["revised_prompt"]
        }
    
    def _execute_image_analysis(self, task: dict) -> dict:
        \"\"\"이미지 분석 실행 - 기존 함수 활용\"\"\"
        
        image_info = task.get('uploaded_image')
        if not image_info:
            raise ValueError("No image provided for analysis")
        
        # base64 인코딩
        image_base64 = slack_api.get_encoded_image_from_slack(image_info['url'])
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": task['input']},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image_info['mimetype']};base64,{image_base64}"
                    }
                }
            ]
        }]
        
        response = openai_api.generate_chat_completion(
            messages=messages,
            user=self.context.get('user_id', 'unknown'),
            stream=False
        )
        
        return {
            'type': 'analysis',
            'content': response.choices[0].message.content
        }
    
    def _contains_korean(self, text: str) -> bool:
        \"\"\"한국어 포함 여부 확인\"\"\"
        return any('가' <= char <= '힣' for char in text)
```

## 구현 순서

### Phase 1: 기본 구조 (1주)
1. `WorkflowEngine` 클래스 기본 구조
2. `TaskExecutor` 클래스 구현  
3. 기존 `MessageHandler`에 통합

### Phase 2: 안정화 (1주)
1. 에러 처리 및 fallback 로직
2. 진행 상황 표시 개선
3. 성능 최적화

### Phase 3: 테스트 (3일)
1. 다양한 시나리오 테스트
2. 기존 기능 호환성 검증
3. 사용자 피드백 반영

이 문서에 따라 구현하면 원하는 5단계 워크플로우가 완성됩니다!
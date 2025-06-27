# 작업 나열/수행/취합 설계

## 2단계: 작업 나열

### 목표
1단계에서 분석된 의도를 구체적인 실행 가능한 작업들로 변환

### 작업 변환 함수

```python
def create_task_list(intent_data: dict, context: dict) -> list:
    \"\"\"의도 분석 결과를 실행 가능한 작업 목록으로 변환\"\"\"
    
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
        if task['type'] == 'image_analysis' and context.get('uploaded_image'):
            task['input'] = {
                'text': task['input'],
                'image': context['uploaded_image']
            }
        elif task['type'] in ['text_generation', 'image_generation']:
            # 스레드 컨텍스트 추가
            if context.get('thread_messages'):
                task['context'] = context['thread_messages']
        
        tasks.append(task)
    
    # 우선순위와 의존성에 따라 정렬
    return sort_tasks_by_dependency(tasks)

def sort_tasks_by_dependency(tasks: list) -> list:
    \"\"\"의존성을 고려하여 작업 순서 정렬\"\"\"
    
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
```

## 3단계: 작업 수행

### 작업 실행 엔진

```python
class TaskExecutor:
    def __init__(self, app, user_context):
        self.app = app
        self.user_context = user_context
        
    def execute_task_list(self, tasks: list) -> dict:
        \"\"\"작업 목록 실행\"\"\"
        
        results = {}
        
        for task in tasks:
            try:
                # 의존성 체크
                if not self._check_dependencies(task, results):
                    task['status'] = 'failed'
                    task['error'] = 'Dependencies not met'
                    continue
                
                # 작업 실행
                task['status'] = 'running'
                start_time = time.time()
                
                result = self._execute_single_task(task)
                
                task['status'] = 'completed'
                task['result'] = result
                task['execution_time'] = time.time() - start_time
                
                results[task['id']] = task
                
            except Exception as e:
                task['status'] = 'failed'
                task['error'] = str(e)
                task['execution_time'] = time.time() - start_time if 'start_time' in locals() else 0
                
                logger.log_error(f"Task {task['id']} failed", e)
                results[task['id']] = task
        
        return results
    
    def _execute_single_task(self, task: dict):
        \"\"\"개별 작업 실행\"\"\"
        
        task_type = task['type']
        
        if task_type == 'text_generation':
            return self._execute_text_generation(task)
        elif task_type == 'image_generation':
            return self._execute_image_generation(task)
        elif task_type == 'image_analysis':
            return self._execute_image_analysis(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _execute_text_generation(self, task: dict):
        \"\"\"텍스트 생성 작업 실행\"\"\"
        
        # 메시지 준비
        messages = [{"role": "user", "content": task['input']}]
        
        # 컨텍스트 추가 (스레드 메시지)
        if 'context' in task and task['context']:
            context_messages = []
            for msg in task['context']:
                role = "assistant" if msg.get("bot_id") else "user"
                content = f"{msg.get('user_name', 'User')}: {msg.get('text', '')}"
                context_messages.append({"role": role, "content": content})
            
            messages = context_messages + messages
        
        # OpenAI API 호출
        response = openai_api.generate_chat_completion(
            messages=messages,
            user=self.user_context.get('user_id', 'unknown'),
            stream=False
        )
        
        return {
            'type': 'text',
            'content': response.choices[0].message.content,
            'model': 'gpt-4o'
        }
    
    def _execute_image_generation(self, task: dict):
        \"\"\"이미지 생성 작업 실행\"\"\"
        
        # 이미지 프롬프트 준비 (영어로 변환)
        if self._is_korean(task['input']):
            prompt_conversion = f\"\"\"
다음 한국어 요청을 DALL-E 이미지 생성을 위한 영어 프롬프트로 변환해주세요:
"{task['input']}"

영어 프롬프트만 반환하세요:
\"\"\"
            
            response = openai_api.generate_chat_completion(
                messages=[{"role": "user", "content": prompt_conversion}],
                user=self.user_context.get('user_id', 'unknown'),
                stream=False
            )
            
            english_prompt = response.choices[0].message.content.strip()
        else:
            english_prompt = task['input']
        
        # DALL-E 이미지 생성
        image_result = openai_api.generate_image(english_prompt)
        
        # 이미지 다운로드
        image_data = slack_api.get_image_from_slack(image_result["image_url"])
        
        return {
            'type': 'image',
            'image_url': image_result["image_url"],
            'image_data': image_data,
            'revised_prompt': image_result["revised_prompt"],
            'original_prompt': task['input']
        }
    
    def _execute_image_analysis(self, task: dict):
        \"\"\"이미지 분석 작업 실행\"\"\"
        
        input_data = task['input']
        
        # 이미지와 텍스트 준비
        if isinstance(input_data, dict):
            text = input_data['text']
            image_info = input_data['image']
        else:
            text = input_data
            image_info = self.user_context.get('uploaded_image')
        
        # 이미지를 base64로 인코딩
        image_base64 = slack_api.get_encoded_image_from_slack(image_info['url'])
        
        # GPT-4 Vision으로 이미지 분석
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": text},
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
            user=self.user_context.get('user_id', 'unknown'),
            stream=False
        )
        
        return {
            'type': 'analysis',
            'content': response.choices[0].message.content,
            'analyzed_image': image_info
        }
    
    def _check_dependencies(self, task: dict, completed_results: dict) -> bool:
        \"\"\"작업 의존성 확인\"\"\"
        
        for dep_id in task['dependencies']:
            if dep_id not in completed_results:
                return False
            if completed_results[dep_id]['status'] != 'completed':
                return False
        
        return True
    
    def _is_korean(self, text: str) -> bool:
        \"\"\"한국어 텍스트 판별\"\"\"
        korean_chars = sum(1 for char in text if '가' <= char <= '힣')
        return korean_chars > len(text) * 0.3
```

## 4단계: 작업 취합

### 결과 통합 함수

```python
def aggregate_task_results(task_results: dict, original_intent: dict) -> dict:
    \"\"\"작업 결과들을 통합\"\"\"
    
    # 성공한 작업들과 실패한 작업들 분류
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
                'task_id': task_id,
                'content': result['content'],
                'description': task['description']
            })
        elif result['type'] == 'image':
            image_results.append({
                'task_id': task_id,
                'image_url': result['image_url'],
                'image_data': result['image_data'],
                'prompt': result['revised_prompt'],
                'description': task['description']
            })
        elif result['type'] == 'analysis':
            analysis_results.append({
                'task_id': task_id,
                'content': result['content'],
                'description': task['description']
            })
    
    # 실행 통계
    total_time = sum(task.get('execution_time', 0) for task in task_results.values())
    
    return {
        'original_intent': original_intent['user_intent'],
        'execution_summary': {
            'total_tasks': len(task_results),
            'successful_tasks': len(successful_tasks),
            'failed_tasks': len(failed_tasks),
            'total_execution_time': total_time
        },
        'results': {
            'text_content': text_results,
            'images': image_results,
            'analyses': analysis_results
        },
        'errors': [
            {
                'task_id': task_id,
                'description': task['description'],
                'error': task['error']
            }
            for task_id, task in failed_tasks.items()
        ]
    }
```

## 5단계: 회신

### 최종 응답 생성

```python
def generate_final_response(aggregated_results: dict) -> dict:
    \"\"\"취합된 결과를 최종 응답으로 변환\"\"\"
    
    # OpenAI에게 결과 정리 요청
    summary_prompt = create_response_summary_prompt(aggregated_results)
    
    try:
        formatted_response = openai_api.generate_chat_completion(
            messages=[{"role": "user", "content": summary_prompt}],
            user="response_generator",
            stream=False
        )
        
        final_text = formatted_response.choices[0].message.content
        
    except Exception as e:
        logger.log_error("Response formatting failed", e)
        # Fallback: 간단한 결과 정리
        final_text = create_simple_response_summary(aggregated_results)
    
    return {
        'text_response': final_text,
        'attachments': {
            'images': aggregated_results['results']['images'],
            'files': []
        },
        'metadata': aggregated_results['execution_summary']
    }

def create_response_summary_prompt(results: dict) -> str:
    \"\"\"응답 정리를 위한 프롬프트 생성\"\"\"
    
    text_content = results['results']['text_content']
    images = results['results']['images'] 
    analyses = results['results']['analyses']
    errors = results['errors']
    
    prompt = f\"\"\"
다음은 사용자 요청 "{results['original_intent']}"에 대한 처리 결과입니다:

텍스트 결과:
{chr(10).join([f"- {item['description']}: {item['content'][:200]}..." for item in text_content])}

이미지 결과:
{chr(10).join([f"- {item['description']}: 이미지 생성됨 (프롬프트: {item['prompt']})" for item in images])}

분석 결과:
{chr(10).join([f"- {item['description']}: {item['content'][:200]}..." for item in analyses])}

오류:
{chr(10).join([f"- {error['description']}: {error['error']}" for error in errors]) if errors else "없음"}

이 결과들을 사용자에게 친근하고 이해하기 쉽게 정리해서 하나의 통합된 응답으로 만들어주세요.
이미지가 생성되었다면 "이미지를 생성했습니다"라고 언급하고, 별도로 업로드된다고 설명하세요.
오류가 있다면 자연스럽게 언급하되 과도하게 강조하지 마세요.
\"\"\"
    
    return prompt

def create_simple_response_summary(results: dict) -> str:
    \"\"\"간단한 응답 요약 (fallback)\"\"\"
    
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
    
    return "\\n\\n".join(parts)
```

### Slack 전송

```python
def send_final_response_to_slack(response_data: dict, slack_context: dict):
    \"\"\"최종 응답을 Slack으로 전송\"\"\"
    
    # 텍스트 응답 전송
    slack_api.send_message(
        app=slack_context["app"],
        channel=slack_context["channel"],
        text=response_data["text_response"],
        thread_ts=slack_context.get("thread_ts")
    )
    
    # 이미지들 업로드
    for i, image in enumerate(response_data["attachments"]["images"]):
        filename = f"generated_image_{i+1}.png"
        slack_api.upload_file(
            app=slack_context["app"],
            channel=slack_context["channel"],
            file_data=image["image_data"],
            filename=filename,
            thread_ts=slack_context.get("thread_ts")
        )
```

이 설계를 통해 복잡한 복합 요청도 체계적으로 처리할 수 있습니다.
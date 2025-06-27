# OpenAI 기반 사용자 의도 분석 설계

## 1단계: 사용자 의도 파악

### 목표
사용자 메시지와 봇의 능력 목록을 OpenAI에게 전달하여 필요한 작업들을 식별

### OpenAI 프롬프트 설계

```python
def create_intent_analysis_prompt(user_message: str, context: dict) -> str:
    capabilities = \"\"\"
봇이 할 수 있는 작업들:

1. 텍스트 생성 및 대화
   - 질문 답변, 설명, 요약
   - 번역 (한국어 ↔ 영어)  
   - 코드 생성 및 설명
   - 창작 글쓰기 (시, 에세이, 이야기)
   - 문서 작성 (보고서, 계획서)
   - 데이터 분석 및 해석

2. 이미지 생성
   - DALL-E를 통한 다양한 스타일의 이미지 생성
   - 로고, 일러스트, 개념 시각화

3. 이미지 분석  
   - 이미지 내용 설명
   - 차트, 그래프 분석
   - 코드 스크린샷 해석
   - 문서 이미지 읽기

4. 메시지 관리
   - 메시지 전송, 수정, 삭제
   - 파일 업로드 및 다운로드

5. 대화 컨텍스트 활용
   - 스레드 내 이전 대화 참조
   - 사용자 정보 조회
\"\"\"

    return f\"\"\"
사용자 메시지: "{user_message}"

대화 컨텍스트:
- 사용자: {context.get('user_name', 'Unknown')}
- 스레드 길이: {context.get('thread_length', 0)}개 메시지
- 첨부 이미지: {context.get('has_image', False)}

봇의 능력: {capabilities}

위 사용자 메시지를 분석하여 필요한 작업들을 JSON 형태로 응답해주세요:

{{
    "user_intent": "사용자가 원하는 것에 대한 간단한 설명",
    "required_tasks": [
        {{
            "task_id": "unique_identifier",
            "task_type": "작업 유형 (text_generation, image_generation, image_analysis 등)",
            "description": "구체적인 작업 설명",
            "input_data": "작업에 필요한 입력 데이터",
            "priority": 1-10,
            "depends_on": ["의존하는 다른 작업의 task_id들"]
        }}
    ],
    "execution_strategy": "sequential 또는 parallel",
    "estimated_time": "예상 소요 시간 (초)"
}}

예시:
- "파이썬 설명해줘" → text_generation 작업 1개
- "고양이 그려줘" → image_generation 작업 1개  
- "AI 설명하고 로봇 이미지도 그려줘" → text_generation + image_generation 작업 2개
- [이미지 첨부] "이 차트 분석해줘" → image_analysis 작업 1개

JSON만 응답하세요.
\"\"\"
```

### 응답 파싱 함수

```python
import json
import re

def parse_intent_analysis(openai_response: str) -> dict:
    \"\"\"OpenAI 응답에서 JSON 추출 및 파싱\"\"\"
    
    try:
        # JSON 코드 블록 제거
        content = re.sub(r'```json\\n|```\\n|```', '', openai_response)
        
        # JSON 파싱
        result = json.loads(content.strip())
        
        # 필수 필드 검증
        required_fields = ['user_intent', 'required_tasks']
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
        
        # 작업 필드 검증
        for task in result['required_tasks']:
            required_task_fields = ['task_id', 'task_type', 'description']
            for field in required_task_fields:
                if field not in task:
                    raise ValueError(f"Missing task field: {field}")
        
        return result
        
    except (json.JSONDecodeError, ValueError) as e:
        logger.log_error("Intent analysis parsing failed", e)
        
        # Fallback: 기본 의도 분석
        return create_fallback_intent(openai_response)

def create_fallback_intent(response_text: str) -> dict:
    \"\"\"파싱 실패 시 기본 의도 분석\"\"\"
    
    # 키워드 기반 간단한 분석
    if "그려" in response_text or "이미지" in response_text:
        return {
            "user_intent": "이미지 생성 요청",
            "required_tasks": [{
                "task_id": "fallback_image",
                "task_type": "image_generation", 
                "description": "이미지 생성",
                "input_data": response_text,
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
                "input_data": response_text,
                "priority": 1,
                "depends_on": []
            }],
            "execution_strategy": "sequential", 
            "estimated_time": "10"
        }
```

### 실제 구현 함수

```python
def analyze_user_intent(self, user_message: str, context: dict) -> dict:
    \"\"\"1단계: 사용자 의도 파악\"\"\"
    
    try:
        # OpenAI에게 의도 분석 요청
        prompt = create_intent_analysis_prompt(user_message, context)
        
        response = openai_api.generate_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            user=context.get('user_id', 'unknown'),
            stream=False,
            temperature=0.1  # 일관된 분석을 위해 낮은 온도
        )
        
        content = response.choices[0].message.content
        
        # JSON 파싱
        intent_data = parse_intent_analysis(content)
        
        logger.log_info("Intent analysis completed", {
            "user_intent": intent_data["user_intent"],
            "task_count": len(intent_data["required_tasks"])
        })
        
        return intent_data
        
    except Exception as e:
        logger.log_error("Intent analysis failed", e)
        
        # Fallback: 기존 방식 사용
        return create_fallback_intent(user_message)
```

## 응답 예시

### 단순 요청
**입력**: "파이썬이 뭐야?"
**응답**:
```json
{
    "user_intent": "파이썬 프로그래밍 언어에 대한 설명 요청",
    "required_tasks": [
        {
            "task_id": "explain_python",
            "task_type": "text_generation",
            "description": "파이썬 프로그래밍 언어 설명",
            "input_data": "파이썬이 뭐야?",
            "priority": 1,
            "depends_on": []
        }
    ],
    "execution_strategy": "sequential",
    "estimated_time": "5"
}
```

### 복합 요청
**입력**: "AI에 대해 설명하고 로봇 이미지도 그려줘"
**응답**:
```json
{
    "user_intent": "AI 설명과 로봇 이미지 생성 요청",
    "required_tasks": [
        {
            "task_id": "explain_ai",
            "task_type": "text_generation", 
            "description": "AI(인공지능)에 대한 설명",
            "input_data": "AI에 대해 설명해줘",
            "priority": 1,
            "depends_on": []
        },
        {
            "task_id": "draw_robot",
            "task_type": "image_generation",
            "description": "로봇 이미지 생성",
            "input_data": "AI robot, futuristic design",
            "priority": 2, 
            "depends_on": []
        }
    ],
    "execution_strategy": "parallel",
    "estimated_time": "15"
}
```

### 이미지 분석 요청
**입력**: [이미지 첨부] "이 차트가 뭘 의미해?"
**응답**:
```json
{
    "user_intent": "차트 이미지 분석 및 해석 요청",
    "required_tasks": [
        {
            "task_id": "analyze_chart",
            "task_type": "image_analysis",
            "description": "차트 이미지 분석 및 의미 해석",
            "input_data": "uploaded_image + 이 차트가 뭘 의미해?",
            "priority": 1,
            "depends_on": []
        }
    ],
    "execution_strategy": "sequential",
    "estimated_time": "8"
}
```

## 에러 처리

### JSON 파싱 실패 시
1. 정규식으로 JSON 부분 추출 재시도
2. 키워드 기반 fallback 분석 사용
3. 기존 방식으로 처리

### OpenAI API 실패 시
1. 재시도 (최대 2회)
2. Fallback 의도 분석 사용
3. 기존 conversation/image_generate 방식으로 처리

### 의도 파악 불가 시
1. 사용자에게 명확화 요청
2. 가장 가능성 높은 작업으로 처리
3. 에러 메시지와 함께 기본 대화 모드로 전환
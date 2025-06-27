# AI SDK 통합 가이드

이 문서는 Slack AI 봇에서 사용하는 OpenAI와 Google Gemini SDK의 통합 방법과 구현 세부사항을 설명합니다.

## 📚 SDK 개요

### OpenAI Python SDK
- **패키지**: `openai>=1.6.0`
- **공식 문서**: [python-openai.md](python-openai.md)
- **GitHub**: https://github.com/openai/openai-python
- **주요 기능**: Chat Completions, DALL-E 3, Vision

### Google Gen AI SDK
- **패키지**: `google-genai>=1.22.0`
- **공식 문서**: [python-genai.md](python-genai.md)
- **GitHub**: https://github.com/googleapis/python-genai
- **주요 기능**: Text Generation, Vision (이미지 분석)

## 🏗️ 아키텍처 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    Slack AI Bot                             │
├─────────────────────────────────────────────────────────────┤
│  Workflow Engine (4-Stage Processing)                      │
│  ├─ 1. Intent Analysis    (OpenAI GPT-4o)                  │
│  ├─ 2. Task Planning      (Internal Logic)                 │
│  ├─ 3. Task Execution     (Multi-Model)                    │
│  └─ 4. Result Delivery    (Slack Integration)              │
├─────────────────────────────────────────────────────────────┤
│  Task Executor                                             │
│  ├─ OpenAI Tasks:                                          │
│  │   ├─ text_generation        (GPT-4o)                    │
│  │   ├─ image_generation       (DALL-E 3)                  │
│  │   ├─ image_analysis         (GPT-4 Vision)              │
│  │   └─ thread_summary         (GPT-4o)                    │
│  └─ Gemini Tasks:                                          │
│      ├─ gemini_text_generation   (Gemini 2.0 Flash)       │
│      ├─ gemini_image_analysis    (Gemini Vision)           │
│      ├─ gemini_image_generation  (→ DALL-E fallback)       │
│      └─ gemini_video_generation  (→ Not supported)         │
├─────────────────────────────────────────────────────────────┤
│  API Layer                                                 │
│  ├─ OpenAI API Client    (openai_api.py)                   │
│  └─ Gemini API Client    (gemini_api.py)                   │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure                                            │
│  ├─ AWS Lambda           (Serverless Runtime)              │
│  ├─ DynamoDB             (Context Storage)                 │
│  └─ Slack Bolt           (Event Handling)                  │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 구현 세부사항

### 1. API 클라이언트 초기화

#### OpenAI 클라이언트 (`src/api/openai_api.py`)
```python
from openai import OpenAI

client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    organization=settings.OPENAI_ORG_ID
)
```

#### Gemini 클라이언트 (`src/api/gemini_api.py`)
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=settings.GEMINI_API_KEY)
```

### 2. 환경 변수 설정

#### 필수 환경 변수
```bash
# OpenAI 설정
OPENAI_API_KEY="sk-..."
OPENAI_ORG_ID="org-..."

# Gemini 설정 (둘 중 하나)
GOOGLE_API_KEY="AIza..."
# 또는
GEMINI_API_KEY="AIza..."

# 모델 설정 (선택사항)
OPENAI_MODEL="gpt-4o"
GEMINI_TEXT_MODEL="gemini-2.0-flash-001"
```

#### 설정 로딩 (`src/config/settings.py`)
```python
# Gemini 설정 (GEMINI_API_KEY 또는 GOOGLE_API_KEY 사용 가능)
GEMINI_API_KEY = (
    os.environ.get("GEMINI_API_KEY") or 
    os.environ.get("GOOGLE_API_KEY", "")
).strip()
```

### 3. 작업 실행 로직

#### 작업 타입 매핑 (`src/workflow/task_executor.py`)
```python
def execute_single_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
    task_type = task['type']
    
    # OpenAI 작업
    if task_type == 'text_generation':
        return self._execute_text_generation(task)
    elif task_type == 'image_generation':
        return self._execute_image_generation(task)
    elif task_type == 'image_analysis':
        return self._execute_image_analysis(task)
    
    # Gemini 작업
    elif task_type == 'gemini_text_generation':
        return self._execute_gemini_text_generation(task)
    elif task_type == 'gemini_image_analysis':
        return self._execute_gemini_image_analysis(task)
    
    # 자동 대체 작업
    elif task_type == 'gemini_image_generation':
        # DALL-E로 대체 실행
        return self._execute_image_generation(task)
```

### 4. 메시지 형식 변환

#### OpenAI 호환 형식
```python
messages = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
]
```

#### Gemini 호환 형식
```python
contents = [
    types.Content(
        role="user",  # user 또는 model만 지원
        parts=[types.Part.from_text(text="[System] You are a helpful assistant")]
    ),
    types.Content(
        role="user",
        parts=[types.Part.from_text(text="Hello")]
    )
]
```

### 5. 이미지 처리

#### OpenAI Vision (Base64)
```python
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": prompt},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{image_base64}"
            }
        }
    ]
}]
```

#### Gemini Vision (Parts)
```python
contents = [
    types.Part.from_text(text=prompt),
    types.Part.from_bytes(
        data=image_bytes,
        mime_type="image/png"
    )
]
```

## 🔄 워크플로우 통합

### 1. 의도 분석 단계
```python
# workflow_engine.py
prompt = f"""
사용자 메시지: "{user_message}"
봇의 능력: {capabilities}

다음 작업 타입들을 사용할 수 있습니다:
- text_generation, image_generation, image_analysis, thread_summary
- gemini_text_generation, gemini_image_generation, gemini_video_generation, gemini_image_analysis

JSON으로 응답해주세요:
{{"required_tasks": [...]}}
"""
```

### 2. Fallback 로직
```python
def create_fallback_intent(self, user_message: str, context: Dict[str, Any]):
    if "gemini" in user_message.lower():
        if context.get('uploaded_image'):
            return {"task_type": "gemini_image_analysis"}
        else:
            return {"task_type": "gemini_text_generation"}
    elif "그려" in user_message:
        return {"task_type": "image_generation"}  # DALL-E 사용
```

### 3. 오류 처리 및 재시도
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def api_call_with_retry():
    # API 호출 로직
    pass
```

## 🚀 사용 예시

### 1. 멀티 모델 활용
```
사용자: "Gemini로 머신러닝 설명하고 DALL-E로 다이어그램 그려줘"

워크플로우:
1. Intent Analysis (GPT-4o) → 2개 작업 식별
2. Task 1: gemini_text_generation (Gemini 2.0 Flash)
3. Task 2: image_generation (DALL-E 3)
4. 각각 완료시 즉시 Slack 전송
```

### 2. 자동 대체 처리
```
사용자: "Gemini로 로고 이미지 생성해줘"

처리:
1. gemini_image_generation 작업 생성
2. Gemini 이미지 생성 미지원 감지
3. 자동으로 DALL-E 3으로 대체 실행
4. 대체 실행 로그 기록
```

### 3. 이미지 분석 비교
```
사용자: "두 모델로 이미지 분석 비교해줘" + 이미지 첨부

처리:
1. image_analysis 작업 (GPT-4 Vision)
2. gemini_image_analysis 작업 (Gemini Vision)
3. 두 결과를 각각 별도 메시지로 전송
4. 사용자가 직접 비교 가능
```

## 📊 성능 및 모니터링

### 1. 로깅 시스템
```python
logger.log_info("Gemini 텍스트 생성 완료", {
    "task_id": task['id'],
    "model": "gemini-2.0-flash-001",
    "content_length": len(content),
    "execution_time": time.time() - start_time
})
```

### 2. 오류 추적
```python
try:
    result = gemini_api.generate_text(messages)
except GeminiApiError as e:
    logger.log_error("Gemini API 오류", e, {
        "task_id": task['id'],
        "error_type": type(e).__name__
    })
    # 필요시 OpenAI로 fallback
```

### 3. 사용량 모니터링
- API 호출 횟수 및 토큰 사용량 추적
- 모델별 성능 및 응답 시간 비교
- 오류율 및 재시도 성공률 모니터링

## 🔮 향후 확장 계획

### 1. 추가 모델 지원
- Anthropic Claude 통합
- Azure OpenAI 서비스 지원
- 로컬 모델 (Ollama) 연동

### 2. 기능 확장
- Gemini Imagen 이미지 생성 (SDK 지원시)
- Gemini Veo 비디오 생성 (SDK 지원시)
- 음성 인식 및 생성 (Whisper, TTS)

### 3. 최적화
- 모델별 캐싱 전략
- 비용 최적화 라우팅
- 동적 모델 선택 알고리즘

---

이 통합 가이드는 개발자가 SDK를 활용하여 새로운 AI 기능을 추가하거나 기존 기능을 개선할 때 참고할 수 있는 완전한 구현 참조서입니다.
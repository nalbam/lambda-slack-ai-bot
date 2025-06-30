# AI API 테스트 스위트

이 디렉토리에는 lambda-slack-ai-bot 프로젝트의 모든 AI API를 테스트하는 스크립트들이 포함되어 있습니다.

## 📁 파일 구조

```
src/test/
├── __init__.py                 # 테스트 모듈 초기화
├── test_openai_api.py         # OpenAI API 테스트
├── test_gemini_api.py         # Gemini API 테스트  
├── test_slack_api.py          # Slack API 테스트
├── test_workflow.py           # 워크플로우 엔진 테스트
├── run_all_tests.py          # 통합 테스트 실행기
└── README.md                  # 이 파일
```

## 🚀 사용 방법

### 1. 환경 설정

테스트 실행 전 `.env.local` 파일에 다음 API 키들이 설정되어야 합니다:

```bash
# OpenAI
OPENAI_API_KEY="sk-..."
OPENAI_ORG_ID="org-..."

# Gemini
GEMINI_API_KEY="AIza..."

# Slack
SLACK_BOT_TOKEN="xoxb-..."
SLACK_SIGNING_SECRET="..."
```

### 2. 개별 테스트 실행

각 API를 개별적으로 테스트할 수 있습니다:

```bash
# OpenAI API 테스트
cd src/test
python test_openai_api.py

# Gemini API 테스트  
python test_gemini_api.py

# Slack API 테스트
python test_slack_api.py

# 워크플로우 엔진 테스트
python test_workflow.py
```

### 3. 통합 테스트 실행

모든 테스트를 한 번에 실행:

```bash
cd src/test
python run_all_tests.py
```

## 📋 테스트 내용

### OpenAI API 테스트 (`test_openai_api.py`)

- ✅ **텍스트 생성**: GPT-4o를 사용한 채팅 완료
- ✅ **이미지 생성**: DALL-E 3를 사용한 이미지 생성
- ✅ **이미지 분석**: GPT-4o Vision을 사용한 이미지 분석

### Gemini API 테스트 (`test_gemini_api.py`)

- ✅ **텍스트 생성**: Gemini 2.5 Flash를 사용한 대화
- ✅ **이미지 분석**: Gemini Vision을 사용한 이미지 분석
- ⚠️ **이미지 생성**: Imagen (allowlist 제한)
- ⚠️ **비디오 생성**: Veo (allowlist 제한)  
- ⚠️ **음성 생성**: TTS (allowlist 제한)

### Slack API 테스트 (`test_slack_api.py`)

- ✅ **인증 확인**: 봇 토큰 검증
- ✅ **채널 조회**: 채널 목록 및 정보
- ✅ **API 구조 검증**: 메시지/파일 업로드 구조
- ✅ **유틸리티 함수**: 이미지 인코딩, 파일 업로드 함수

### 워크플로우 엔진 테스트 (`test_workflow.py`)

- ✅ **엔진 초기화**: WorkflowEngine 인스턴스 생성
- ✅ **작업 실행기**: TaskExecutor 기능 검증
- ✅ **Slack 유틸리티**: SlackMessageUtils 검증
- ✅ **시나리오 테스트**: 다양한 요청 시나리오
- ✅ **설정 검증**: 모델 설정 및 API 키 확인

## 📊 테스트 결과

### 성공 예시
```
🚀 AI API 통합 테스트 시작
====================================
📅 시작 시간: 2024-12-28 15:30:25

✅ OPENAI: 9/9 성공 (100.0%)
✅ GEMINI: 6/8 성공 (75.0%)  
✅ SLACK: 8/8 성공 (100.0%)
✅ WORKFLOW: 12/12 성공 (100.0%)

🎉 모든 테스트가 성공적으로 완료되었습니다!
```

### 결과 파일
테스트 완료 후 `test_results_YYYYMMDD_HHMMSS.json` 파일이 생성됩니다:

```json
{
  "timestamp": "2024-12-28 15:30:25",
  "environment": {
    "openai_api_key": true,
    "gemini_api_key": true,
    "slack_bot_token": true
  },
  "tests": [...],
  "summary": {
    "total_test_suites": 4,
    "successful_suites": 4,
    "recommendations": [...]
  }
}
```

## ⚠️ 주의사항

### API 제한사항
- **Gemini Imagen/Veo**: allowlist 기반 접근 제한
- **OpenAI 이미지 생성**: 유료 API (비용 발생)
- **실제 메시지 전송**: 테스트에서는 수행하지 않음

### 환경 요구사항
- Python 3.8+
- 필수 패키지: `python-dotenv`, `slack-sdk`, `google-genai`, `openai`
- 유효한 API 키들

### 테스트 데이터
- 이미지 분석: 공개 Wikipedia 이미지 사용
- 텍스트 생성: 안전한 테스트 프롬프트 사용
- Mock 데이터: 워크플로우 테스트에서 사용

## 🛠️ 문제해결

### 일반적인 오류

1. **API 키 없음**
   ```
   ❌ OPENAI_API_KEY가 설정되지 않았습니다.
   ```
   → `.env.local` 파일에 해당 API 키 추가

2. **모듈 import 실패**
   ```
   ❌ 모듈 import 실패: No module named 'google.genai'
   ```
   → `pip install google-genai` 실행

3. **Gemini allowlist 오류**
   ```
   ⚠️ Gemini 오류 (예상됨): allowlist 뒤에 있어 일반적으로 사용할 수 없습니다.
   ```
   → 정상적인 현상 (Google 승인 필요)

### 로그 확인
테스트 실행 중 상세한 로그가 출력됩니다:
- 요청/응답 시간
- API 응답 구조
- 오류 메시지 및 원인

## 📈 확장 방법

새로운 AI API 테스트 추가 시:

1. `test_new_api.py` 파일 생성
2. `NewAPITester` 클래스 구현
3. `run_all_tests.py`에 테스트 추가
4. 이 README 업데이트

## 🤝 기여

테스트 개선 사항이나 새로운 테스트 케이스가 있다면:
1. 기존 패턴 따르기
2. 안전한 테스트 데이터 사용
3. 적절한 에러 핸들링 포함
4. 문서 업데이트
# 봇 능력 목록

이 문서는 워크플로우 엔진의 1단계(사용자 의도 파악)에서 OpenAI에게 전달되는 봇의 능력 목록입니다.

## 🤖 AI 능력

### 멀티 모델 AI 통합

이 봇은 **OpenAI**와 **Google Gemini** 두 가지 최신 AI 모델을 모두 지원합니다:

- **OpenAI GPT-4o** & **DALL-E 3** - [python-openai.md](python-openai.md) 참조
- **Google Gemini 2.0 Flash** & **Vision** - [python-genai.md](python-genai.md) 참조

### 텍스트 생성 및 대화

**🔥 OpenAI GPT-4o:**
- 고품질 텍스트 생성 및 대화
- 코드 생성 및 설명
- 창작 글쓰기 (시, 에세이, 이야기)
- 실시간 스트리밍 응답

**🆕 Google Gemini 2.5 Flash:**
- 적응형 사고와 비용 효율성 최적화
- 빠른 응답 속도의 텍스트 생성  
- 오디오, 이미지, 비디오, 텍스트 멀티모달 지원
- 한국어 최적화 성능
- 사용법: `"Gemini로 파이썬 설명해줘"`

### 이미지 생성

**🎨 DALL-E 3 (OpenAI):**
- 최고 품질의 이미지 생성
- 다양한 스타일과 아트워크
- HD 품질 1024x1024 이미지
- 한국어 프롬프트 자동 영어 번역

**🆕 Gemini Imagen 4 & 2.0 Flash Image Generation:**
- **Imagen 4**: 최신 고품질 이미지 생성 모델 (`imagen-4.0-generate-preview-06-06`)
- **Gemini 2.0 Flash**: 대화형 이미지 생성 및 편집 (`gemini-2.0-flash-preview-image-generation`)
- allowlist 제한으로 일반 사용자는 DALL-E로 자동 대체

### 이미지 분석

**👁️ GPT-4 Vision (OpenAI):**
- 이미지 내용 상세 설명
- 차트, 그래프 데이터 분석
- 코드 스크린샷 해석
- 문서 이미지 텍스트 읽기

**🆕 Gemini Vision (Google):**
- 고급 이미지 이해 및 분석
- 멀티모달 추론 능력
- 사용법: 이미지 첨부 + `"Gemini로 분석해줘"`

### 스레드 요약 (GPT-4o)
- 스레드 내 모든 메시지 분석 및 요약
- 주요 주제 및 핵심 내용 추출
- 중요한 결정사항이나 결론 강조
- 참여자별 의견 및 관점 정리
- 3-5개 문단으로 간결한 구조화

### 비디오 생성

**🆕 Gemini Veo 2:**
- Google의 최신 고품질 비디오 생성 모델 (`veo-2.0-generate-001`)
- 텍스트와 이미지로부터 비디오 생성 지원
- allowlist 제한으로 일반 사용자는 접근 불가
- 요청시 상세한 안내 메시지 표시

### 음성 생성 (TTS)

**🆕 Gemini TTS:**
- **Gemini 2.5 Flash TTS**: 저지연, 제어 가능한 단일/다중 화자 음성 생성
- **Gemini 2.5 Pro TTS**: 고품질 음성 생성 모델
- 다양한 음성 옵션과 말하기 속도 조절 지원
- allowlist 제한으로 일반 사용자는 접근 불가

## 🔧 사용하는 SDK

### OpenAI Python SDK
- **패키지**: `openai>=1.6.0`
- **문서**: [python-openai.md](python-openai.md)
- **주요 기능**: Chat Completions, DALL-E 3, Vision
- **모델**: `gpt-4o`, `dall-e-3`

### Google Gen AI SDK  
- **패키지**: `google-genai>=1.22.0`
- **문서**: [python-genai.md](python-genai.md)
- **주요 기능**: Text Generation, Vision (이미지 분석)
- **모델**: `gemini-2.5-flash` (기본), `gemini-2.0-flash`, `gemini-1.5-flash`

### 환경 변수 설정
```bash
# OpenAI 설정
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_ORG_ID="your-organization-id"

# Google Gemini 설정 (둘 중 하나)
export GOOGLE_API_KEY="your-google-api-key"
# 또는
export GEMINI_API_KEY="your-gemini-api-key"
```

## 💬 Slack 통합

### 메시지 처리
- 실시간 스트리밍 응답 (800자마다 업데이트)
- 긴 메시지 자동 분할 처리
- 스레드 컨텍스트 유지 및 활용
- 마크다운 → Slack 형식 자동 변환
- 멘션 및 DM 모두 지원

### 파일 및 미디어
- 이미지 즉시 업로드 및 공유
- 업로드된 파일 다운로드 및 분석
- Base64 인코딩 자동 처리
- 다양한 이미지 포맷 지원

### 상호작용
- 채널 멘션 응답
- 다이렉트 메시지 처리
- 스레드 대화 연속성
- 사용자 정보 자동 조회

## 🗄️ 데이터 관리

### 컨텍스트 관리 (DynamoDB)
- 대화 히스토리 저장 및 조회
- 중복 요청 자동 방지
- TTL 기반 자동 정리 (1시간)
- 스레드별 독립적 컨텍스트

## 🔥 고급 기능

### 복합 작업 처리
봇은 다음과 같은 복잡한 요청을 하나의 명령으로 처리할 수 있습니다:

**텍스트 + 이미지 조합:**
- "AI에 대해 설명하고 로봇 이미지도 그려줘"
- "머신러닝 알고리즘을 요약하고 관련 다이어그램도 만들어줘"
- "Gemini로 설명하고 DALL-E로 이미지 그려줘"

**분석 + 생성 조합:**
- "[이미지 업로드] 이 차트를 분석하고 개선 방안도 써줘"
- "[코드 스크린샷] 이 코드를 설명하고 최적화 버전도 작성해줘"
- "[이미지 업로드] Gemini로 분석하고 GPT로 보고서 작성해줘"

**AI 모델 선택:**
- "GPT로 코딩 질문 답변해줘"
- "Gemini로 한국 문화 설명해줘"
- "두 모델로 비교 답변해줘"

**스레드 요약:**
- "스레드 요약해줘"
- "이 토론 내용 정리해줘"
- "회의록 만들어줘"

**다단계 작업:**
- "Python 정렬 알고리즘 설명 → 코드 예시 → 시각화 이미지"
- "회사 로고 디자인 → 설명 → 활용 방안 제시"
- "Gemini로 요약 → GPT로 상세 분석 → DALL-E로 다이어그램"

### 4단계 지능형 워크플로우
1. **의도 분석**: OpenAI가 사용자 요청을 분석하여 필요한 작업들 식별
2. **작업 계획**: 실행 순서와 의존성 고려한 계획 수립
3. **즉시 실행**: 각 작업 완료시 바로 Slack에 결과 전송
4. **완료 알림**: 모든 작업 완료 후 최종 확인

### 성능 특징
- **즉시 응답**: AI 요약 없이 결과 직접 전송
- **병렬 처리**: 독립적 작업들의 동시 실행
- **오류 격리**: 일부 작업 실패시에도 다른 작업 계속 진행
- **메모리 효율**: 스트리밍 기반 처리로 메모리 최적화
- **멀티 모델**: 작업 특성에 따른 최적 AI 모델 선택
- **자동 대체**: 일부 기능 미지원시 다른 모델로 자동 처리
# 봇이 할 수 있는 작업 목록

## OpenAI API 기반 작업

### 1. 텍스트 생성 및 대화
**함수**: `openai_api.generate_chat_completion()`
**기능**:
- 질문 답변
- 텍스트 요약  
- 번역 (한국어 ↔ 영어)
- 코드 생성 및 설명
- 창작 글쓰기 (시, 에세이, 이야기)
- 문서 작성 (보고서, 계획서 등)
- 데이터 분석 및 해석

### 2. 이미지 생성
**함수**: `openai_api.generate_image()`
**기능**:
- DALL-E를 통한 이미지 생성
- 다양한 스타일의 그림 (사실적, 만화, 추상화 등)
- 로고 및 일러스트 생성
- 개념 시각화

**설정 옵션**:
- 품질: standard, hd
- 크기: 1024x1024
- 스타일: vivid, natural

### 3. 이미지 분석
**함수**: `openai_api.generate_chat_completion()` + 이미지 입력
**기능**:
- 이미지 내용 설명
- 차트 및 그래프 분석
- 코드 스크린샷 해석
- 문서 이미지 읽기

## Slack API 기반 작업

### 4. 메시지 관리
**함수들**:
- `slack_api.send_message()` - 메시지 전송
- `slack_api.update_message()` - 메시지 수정
- `slack_api.delete_message()` - 메시지 삭제

### 5. 파일 처리
**함수들**:
- `slack_api.upload_file()` - 파일 업로드
- `slack_api.get_image_from_slack()` - 이미지 다운로드
- `slack_api.get_encoded_image_from_slack()` - 이미지 base64 인코딩

### 6. 사용자 정보 조회
**함수들**:
- `slack_api.get_user_info()` - 사용자 프로필 정보
- `slack_api.get_user_display_name()` - 사용자 표시 이름

### 7. 대화 컨텍스트 관리
**함수들**:
- `slack_api.get_thread_messages()` - 스레드 메시지 조회
- `slack_api.get_reactions()` - 이모지 반응 분석

## DynamoDB 기반 작업

### 8. 데이터 저장 및 조회
**함수들**:
- `context_manager.put_context()` - 대화 컨텍스트 저장
- `context_manager.get_context()` - 컨텍스트 조회
- `context_manager.batch_put_contexts()` - 배치 저장

**기능**:
- 중복 요청 방지
- 대화 히스토리 저장 (TTL: 1시간)
- 사용자별 설정 저장

## 메시지 처리 기능

### 9. 텍스트 포맷팅
**함수들**:
- `slack_api.replace_text()` - 마크다운 → Slack 포맷 변환
- `slack_api.replace_emoji_pattern()` - 이모지 패턴 정리

### 10. 스트리밍 응답
**기능**: 실시간으로 응답을 생성하며 메시지 업데이트

### 11. 메시지 분할
**기능**: Slack 메시지 크기 제한에 따른 자동 분할 처리

## 작업 조합 예시

### 단일 작업
- "파이썬이 뭐야?" → 텍스트 생성
- "고양이 그려줘" → 이미지 생성
- [이미지 첨부] "이게 뭐야?" → 이미지 분석

### 복합 작업 (구현할 대상)
- "AI에 대해 설명하고 로봇 이미지도 그려줘" → 텍스트 생성 + 이미지 생성
- "이 차트 분석하고 요약 보고서 작성해줘" → 이미지 분석 + 텍스트 생성
- "파이썬 장점 설명하고 파이썬 로고도 만들어줘" → 텍스트 생성 + 이미지 생성
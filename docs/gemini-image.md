# Gemini API: 이미지 생성 가이드

공식 문서: [Image Generation - Google Gemini API](https://ai.google.dev/gemini-api/docs/image-generation)

---

## 📌 개요

Gemini API를 사용하면 **텍스트 프론프트 기반 이미지 생성**이 가능합니다.
Google은 두 가지 방식의 이미지 생성 모델을 제공합니다:

* **Gemini (머틸모달)**: 대부분의 일반적인 사용 사례에 권장
* **Imagen (고핵성 특화)**: 고해상드 이미지가 중요한 특수한 경우에 사용

> 모든 생성된 이미지에는 **SynthID 와터링**이 생성됩니다.

---

## 🔐 사용 전 준비

### 지원 모델

* **Gemini**: `gemini-2.0-flash-preview-image-generation`
* **Imagen**: `imagen-3`, `imagen-4`, `imagen-4-ultra`
  ※ Imagen 계열 모델은 \*\*유료 플래(Paid Tier)\*\*에서만 사용 가능

### 사용 가능한 라이브러리

* Gemini와 Imagen 모두 동일한 **Google Generative AI 클라이언트 라이브러리**로 접근 가능

> 일부 국가 및 지역에서는 이미지 생성 기능이 지원되지 않을 수 있습니다.
> [Models 페이지](https://ai.google.dev/models) 참고

---

## 🖼️ Gemini를 이용한 이미지 생성 (Text-to-Image)

Gemini는 **텍스트, 이미지, 혼합 입력**을 지원하는 **대화형 이미지 생성 기능**을 제공합니다.

### 필수 설정

```python
config = types.GenerateContentConfig(
    response_modalities=["TEXT", "IMAGE"]  # 마지막 포함되어야 합니다
)
```

> 이미지 단독 출력은 지원되지 않으며, 텍스트와 함께 응답이 구성됩니다.

---

## 🧪 예제 코드 (Python)

```python
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64

# 클라이언트 초기화
client = genai.Client()

# 프론프트 텍스트 정의
contents = (
    "Hi, can you create a 3d rendered image of a pig "
    "with wings and a top hat flying over a happy "
    "futuristic scifi city with lots of greenery?"
)

# 이미지 생성 요청
response = client.models.generate_content(
    model="gemini-2.0-flash-preview-image-generation",
    contents=contents,
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"]
    )
)

# 결과 처리
for part in response.candidates[0].content.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = Image.open(BytesIO(part.inline_data.data))
        image.save("gemini-native-image.png")
        image.show()
```

---

## ✅ 요약

| 항목          | 설명                                      |
| ----------- | --------------------------------------- |
| 사용 가능 모델    | Gemini 2.0 Flash, Imagen 시리즈            |
| 응답 구성 필수 옵션 | `response_modalities=["TEXT", "IMAGE"]` |
| 출력 형식       | 텍스트 + 인라인 이미지 바이너리                      |
| 사용 제한       | 일부 지역 제한, Imagen은 유료 플래 전용              |
| 와터링         | SynthID 자동 생성                           |

---

## 🔗 참고 링크

* [Gemini API Docs](https://ai.google.dev/gemini-api/docs)
* [Choosing the right model](https://ai.google.dev/docs/overview/models)
* [Google Generative AI Python SDK](https://pypi.org/project/google-generativeai/)

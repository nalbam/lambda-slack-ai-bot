"""
Google Gemini API 래퍼 모듈 - google-genai SDK 사용
"""
import base64
import time
from typing import Dict, Any, List, Optional, Generator, Union
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from src.config import settings
from src.utils import logger


class GeminiApiError(Exception):
    """Gemini API 오류 클래스"""
    pass


class GeminiAPI:
    """Google Gemini API 클라이언트 - google-genai SDK 사용"""
    
    def __init__(self):
        if genai is None or types is None:
            raise ImportError("google-genai package is required. Install with: pip install google-genai")
        
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            logger.log_warning("Gemini API key not configured. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((GeminiApiError, Exception)),
        reraise=True
    )
    def generate_text(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
        """Gemini를 사용하여 텍스트를 생성합니다.
        
        Args:
            messages: 대화 메시지 목록
            model: 사용할 모델 (기본값: settings.GEMINI_TEXT_MODEL)
            temperature: 생성 온도 (0.0~1.0)
            max_tokens: 최대 토큰 수
            stream: 스트리밍 사용 여부
            
        Returns:
            Gemini API 응답 또는 스트림 객체
            
        Raises:
            GeminiApiError: API 호출 중 오류 발생 시
        """
        if model is None:
            model = settings.GEMINI_TEXT_MODEL
            
        if not self.client:
            raise GeminiApiError(
                "❌ Gemini API를 사용할 수 없습니다.\n"
                "🔑 GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경 변수를 설정해주세요.\n"
                "📖 https://aistudio.google.com/apikey 에서 API 키를 발급받을 수 있습니다."
            )
            
        try:
            # 메시지를 Gemini 형식으로 변환
            contents = self._convert_messages_to_contents(messages)
            
            # 생성 설정
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                candidate_count=1
            )
            
            logger.log_info("Gemini 텍스트 생성 요청", {
                "model": model,
                "messages_count": len(messages),
                "stream": stream,
                "temperature": temperature,
                "max_tokens": max_tokens
            })
            
            # google-genai SDK 사용
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            
            if stream:
                # 스트리밍은 현재 구현하지 않음
                logger.log_warning("스트리밍은 현재 지원되지 않음, 일반 응답으로 처리")
            
            # 응답을 표준 형식으로 변환
            result = {
                "candidates": [{
                    "content": {
                        "parts": [{"text": response.text}]
                    }
                }]
            }
            
            logger.log_info("Gemini 텍스트 생성 완료", {
                "response_length": len(response.text) if response.text else 0
            })
            return result
                
        except Exception as e:
            logger.log_error("Gemini 텍스트 생성 중 오류 발생", e, {
                "model": model,
                "messages_count": len(messages),
                "temperature": temperature
            })
            
            # API 키 오류인 경우 더 명확한 메시지 제공
            if "API key not valid" in str(e) or "INVALID_ARGUMENT" in str(e):
                raise GeminiApiError(
                    "❌ Gemini API 키가 유효하지 않습니다.\n"
                    "🔑 올바른 GEMINI_API_KEY 또는 GOOGLE_API_KEY를 설정해주세요.\n"
                    "📖 https://aistudio.google.com/apikey 에서 새 API 키를 발급받을 수 있습니다."
                )
            
            raise GeminiApiError(f"Gemini 텍스트 생성 오류: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((GeminiApiError, Exception)),
        reraise=True
    )
    def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        aspect_ratio: str = "1:1",
        person_generation: str = "allow_adult"
    ) -> Dict[str, Any]:
        """Gemini Imagen을 사용하여 이미지를 생성합니다.
        
        Args:
            prompt: 이미지 생성 프롬프트
            model: 사용할 모델 (기본값: imagen-4.0-generate-preview-06-06 또는 gemini-2.0-flash-preview-image-generation)
            aspect_ratio: 이미지 비율 (1:1, 9:16, 16:9, 4:3, 3:4)
            person_generation: 인물 생성 설정
            
        Returns:
            생성된 이미지 정보
            
        Raises:
            GeminiApiError: API 호출 중 오류 발생 시
        """
        if model is None:
            model = settings.GEMINI_IMAGE_MODEL
            
        if not self.client:
            raise GeminiApiError(
                "❌ Gemini API를 사용할 수 없습니다.\n"
                "🔑 GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경 변수를 설정해주세요.\n"
                "📖 https://aistudio.google.com/apikey 에서 API 키를 발급받을 수 있습니다."
            )
            
        try:
            logger.log_info("Gemini 이미진 생성 요청", {
                "model": model,
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "aspect_ratio": aspect_ratio,
                "person_generation": person_generation
            })
            
            # 모든 이미지 생성은 generate_images API 사용
            config = types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                person_generation=person_generation
            )
            
            response = self.client.models.generate_images(
                model=model,
                prompt=prompt,
                config=config
            )
            
            candidates = response.candidates if hasattr(response, 'candidates') else []
            logger.log_info("Gemini 이미지 생성 완료", {
                "candidates_count": len(candidates)
            })
            return {
                "candidates": candidates,
                "images": candidates
            }
                
        except Exception as e:
            logger.log_error("Gemini 이미지 생성 중 오류 발생", e, {
                "model": model,
                "prompt_length": len(prompt),
                "aspect_ratio": aspect_ratio
            })
            
            # 지원되지 않는 기능인 경우 DALL-E 대체 사용 안내
            if "not enabled" in str(e) or "not supported" in str(e) or "allowlist" in str(e) or "403" in str(e):
                raise GeminiApiError(
                    "⚠️ Gemini Imagen 이미지 생성은 현재 allowlist 뒤에 있어 일반적으로 사용할 수 없습니다.\n"
                    "🎨 DALL-E 3를 사용한 이미지 생성으로 자동 대체됩니다."
                )
            
            # API 키 오류인 경우 더 명확한 메시지 제공
            if "API key not valid" in str(e) or "INVALID_ARGUMENT" in str(e):
                raise GeminiApiError(
                    "❌ Gemini API 키가 유효하지 않습니다.\n"
                    "🔑 올바른 GEMINI_API_KEY 또는 GOOGLE_API_KEY를 설정해주세요.\n"
                    "📖 https://aistudio.google.com/apikey 에서 새 API 키를 발급받을 수 있습니다."
                )
            
            raise GeminiApiError(f"Gemini 이미지 생성 오류: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((GeminiApiError, Exception)),
        reraise=True
    )
    def generate_video(
        self,
        prompt: str,
        model: Optional[str] = None,
        duration_seconds: int = 5,
        aspect_ratio: str = "16:9"
    ) -> Dict[str, Any]:
        """Gemini Veo를 사용하여 비디오를 생성합니다.
        
        Args:
            prompt: 비디오 생성 프롬프트
            model: 사용할 모델 (기본값: veo-2.0-generate-001)
            duration_seconds: 비디오 길이 (초)
            aspect_ratio: 비디오 비율
            
        Returns:
            생성된 비디오 정보
            
        Raises:
            GeminiApiError: API 호출 중 오류 발생 시
        """
        if model is None:
            model = settings.GEMINI_VIDEO_MODEL
            
        if not self.client:
            raise GeminiApiError(
                "❌ Gemini API를 사용할 수 없습니다.\n"
                "🔑 GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경 변수를 설정해주세요.\n"
                "📖 https://aistudio.google.com/apikey 에서 API 키를 발급받을 수 있습니다."
            )
            
        try:
            logger.log_info("Gemini 비디오 생성 요청", {
                "model": model,
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "duration": duration_seconds,
                "aspect_ratio": aspect_ratio
            })
            
            # Veo 비디오 생성 설정
            config = types.GenerateVideosConfig(
                number_of_videos=1,
                fps=24,
                duration_seconds=duration_seconds,
                enhance_prompt=True,
                aspect_ratio=aspect_ratio
            )
            
            # Veo API 호출 (비동기 작업)
            operation = self.client.models.generate_videos(
                model=model,
                prompt=prompt,
                config=config
            )
            
            operation_name = operation.name if hasattr(operation, 'name') else 'unknown'
            logger.log_info("Gemini 비디오 생성 작업 시작됨", {
                "operation_name": operation_name,
                "duration": duration_seconds
            })
            return {
                "operation": operation,
                "status": "processing",
                "message": "비디오 생성이 시작되었습니다. 완료까지 시간이 걸릴 수 있습니다."
            }
                
        except Exception as e:
            logger.log_error("Gemini 비디오 생성 중 오류 발생", e, {
                "model": model,
                "prompt_length": len(prompt),
                "duration": duration_seconds
            })
            
            # 지원되지 않는 기능인 경우 안내
            if "not enabled" in str(e) or "not supported" in str(e) or "allowlist" in str(e) or "403" in str(e):
                raise GeminiApiError(
                    "⚠️ Gemini Veo 비디오 생성은 현재 allowlist 뒤에 있어 일반적으로 사용할 수 없습니다.\n"
                    "🎬 이 기능은 Google에서 승인된 개발자만 사용할 수 있습니다."
                )
            
            # API 키 오류인 경우 더 명확한 메시지 제공
            if "API key not valid" in str(e) or "INVALID_ARGUMENT" in str(e):
                raise GeminiApiError(
                    "❌ Gemini API 키가 유효하지 않습니다.\n"
                    "🔑 올바른 GEMINI_API_KEY 또는 GOOGLE_API_KEY를 설정해주세요.\n"
                    "📖 https://aistudio.google.com/apikey 에서 새 API 키를 발급받을 수 있습니다."
                )
            
            raise GeminiApiError(f"Gemini 비디오 생성 오류: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((GeminiApiError, Exception)),
        reraise=True
    )
    def generate_speech(
        self,
        text: str,
        model: Optional[str] = None,
        voice: str = "en-US-Journey-D",
        speaking_rate: float = 1.0
    ) -> Dict[str, Any]:
        """Gemini TTS를 사용하여 음성을 생성합니다.
        
        Args:
            text: 음성으로 변환할 텍스트
            model: 사용할 모델 (기본값: gemini-2.5-flash-preview-tts)
            voice: 음성 타입
            speaking_rate: 말하기 속도
            
        Returns:
            생성된 음성 정보
            
        Raises:
            GeminiApiError: API 호출 중 오류 발생 시
        """
        if model is None:
            model = "gemini-2.5-flash-preview-tts"
            
        if not self.client:
            raise GeminiApiError(
                "❌ Gemini API를 사용할 수 없습니다.\n"
                "🔑 GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경 변수를 설정해주세요.\n"
                "📖 https://aistudio.google.com/apikey 에서 API 키를 발급받을 수 있습니다."
            )
            
        try:
            logger.log_info("Gemini TTS 요청", {
                "model": model,
                "text": text[:100] + "..." if len(text) > 100 else text,
                "voice": voice
            })
            
            # TTS 설정
            config = types.GenerateContentConfig(
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice
                        )
                    ),
                    speaking_rate=speaking_rate
                )
            )
            
            contents = [types.Content(
                role="user",
                parts=[types.Part.from_text(text=text)]
            )]
            
            # TTS API 호출
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            
            logger.log_info("Gemini TTS 완료")
            return {
                "audio_data": response.candidates[0] if hasattr(response, 'candidates') and response.candidates else None,
                "voice": voice,
                "text": text
            }
                
        except Exception as e:
            logger.log_error("Gemini TTS 중 오류 발생", e)
            
            # 지원되지 않는 기능인 경우 안내
            if "not enabled" in str(e) or "not supported" in str(e) or "allowlist" in str(e) or "403" in str(e):
                raise GeminiApiError(
                    "⚠️ Gemini TTS는 현재 allowlist 뒤에 있어 일반적으로 사용할 수 없습니다.\n"
                    "🎵 이 기능은 Google에서 승인된 개발자만 사용할 수 있습니다."
                )
            
            # API 키 오류인 경우 더 명확한 메시지 제공
            if "API key not valid" in str(e) or "INVALID_ARGUMENT" in str(e):
                raise GeminiApiError(
                    "❌ Gemini API 키가 유효하지 않습니다.\n"
                    "🔑 올바른 GEMINI_API_KEY 또는 GOOGLE_API_KEY를 설정해주세요.\n"
                    "📖 https://aistudio.google.com/apikey 에서 새 API 키를 발급받을 수 있습니다."
                )
            
            raise GeminiApiError(f"Gemini TTS 오류: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((GeminiApiError, Exception)),
        reraise=True
    )
    def analyze_image(
        self,
        image_data: str,
        prompt: str,
        model: Optional[str] = None,
        mime_type: str = "image/png"
    ) -> Dict[str, Any]:
        """Gemini Vision을 사용하여 이미지를 분석합니다.
        
        Args:
            image_data: Base64 인코딩된 이미지 데이터
            prompt: 분석 요청 프롬프트
            model: 사용할 모델 (기본값: settings.GEMINI_TEXT_MODEL)
            mime_type: 이미지 MIME 타입
            
        Returns:
            이미지 분석 결과
            
        Raises:
            GeminiApiError: API 호출 중 오류 발생 시
        """
        if model is None:
            model = settings.GEMINI_TEXT_MODEL
            
        if not self.client:
            raise GeminiApiError(
                "❌ Gemini API를 사용할 수 없습니다.\n"
                "🔑 GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경 변수를 설정해주세요.\n"
                "📖 https://aistudio.google.com/apikey 에서 API 키를 발급받을 수 있습니다."
            )
            
        try:
            # Base64 데이터를 바이너리로 변환
            image_bytes = base64.b64decode(image_data)
            
            # 이미지 파트 생성
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
            
            # 텍스트 파트 생성
            text_part = types.Part.from_text(text=prompt)
            
            # 컨텐츠 생성 (텍스트 + 이미지)
            contents = [text_part, image_part]
            
            logger.log_info("Gemini 이미지 분석 요청", {
                "model": model,
                "prompt": prompt[:100]
            })
            
            # google-genai SDK 사용
            response = self.client.models.generate_content(
                model=model,
                contents=contents
            )
            
            # 응답을 표준 형식으로 변환
            result = {
                "candidates": [{
                    "content": {
                        "parts": [{"text": response.text}]
                    }
                }]
            }
            
            logger.log_info("Gemini 이미지 분석 완료")
            return result
            
        except Exception as e:
            logger.log_error("Gemini 이미지 분석 중 오류 발생", e)
            
            # API 키 오류인 경우 더 명확한 메시지 제공
            if "API key not valid" in str(e) or "INVALID_ARGUMENT" in str(e):
                raise GeminiApiError(
                    "❌ Gemini API 키가 유효하지 않습니다.\n"
                    "🔑 올바른 GEMINI_API_KEY 또는 GOOGLE_API_KEY를 설정해주세요.\n"
                    "📖 https://aistudio.google.com/apikey 에서 새 API 키를 발급받을 수 있습니다."
                )
            
            raise GeminiApiError(f"Gemini 이미지 분석 오류: {str(e)}")
    
    def _convert_messages_to_contents(self, messages: List[Dict[str, Any]]) -> List[Any]:
        """OpenAI 스타일 메시지를 Gemini Contents로 변환합니다."""
        contents = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            # Gemini에서 지원하는 role: user, model
            if role in ["user", "system"]:
                gemini_role = "user"
            elif role == "assistant":
                gemini_role = "model"
            else:
                gemini_role = "user"  # 기본값
            
            # role prefix 추가 (system 메시지 구분을 위해)
            if role == "system":
                content = f"[System] {content}"
            
            contents.append(types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=content)]
            ))
        
        return contents
    
    
    
    def extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """Gemini 응답에서 텍스트를 추출합니다."""
        try:
            if "candidates" not in response or not response["candidates"]:
                return ""
            
            candidate = response["candidates"][0]
            if "content" not in candidate or "parts" not in candidate["content"]:
                return ""
            
            parts = candidate["content"]["parts"]
            text_parts = [part.get("text", "") for part in parts if "text" in part]
            
            return "".join(text_parts)
            
        except Exception as e:
            logger.log_error("Gemini 응답 텍스트 추출 중 오류", e)
            return ""


# 전역 인스턴스
gemini_api = GeminiAPI()


# 편의를 위한 함수들
def generate_text_with_gemini(
    messages: List[Dict[str, Any]],
    user: str,
    stream: bool = False,
    temperature: float = 0.7
) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
    """Gemini를 사용한 텍스트 생성 (OpenAI API와 호환)"""
    return gemini_api.generate_text(
        messages=messages,
        temperature=temperature,
        stream=stream
    )


def generate_image_with_gemini(prompt: str) -> Dict[str, Any]:
    """Gemini Imagen을 사용한 이미지 생성 (현재 지원되지 않음)"""
    raise GeminiApiError("이미지 생성은 현재 지원되지 않습니다. DALL-E를 사용해주세요.")


def generate_video_with_gemini(prompt: str, duration: int = 5) -> Dict[str, Any]:
    """Gemini Veo를 사용한 비디오 생성 (현재 지원되지 않음)"""
    raise GeminiApiError("비디오 생성은 현재 지원되지 않습니다.")


def analyze_image_with_gemini(image_data: str, prompt: str, mime_type: str = "image/png") -> Dict[str, Any]:
    """Gemini Vision을 사용한 이미지 분석"""
    return gemini_api.analyze_image(image_data, prompt, mime_type=mime_type)
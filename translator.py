"""번역 로직: 설정 조회, 입력 검증, OpenAI 호출. UI 의존성 없음(설정 조회의 st.secrets 제외)."""
import os

import openai
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MAX_CHARS = 2000
DEFAULT_MODEL = "gpt-6.1-sol"
TIMEOUT_SECONDS = 30

LANGUAGES = {
    "영어": "English",
    "일본어": "Japanese",
    "중국어": "Chinese (Simplified)",
}

SYSTEM_PROMPT = (
    "You are a professional translator. Translate the user's text into {target_language}. "
    "Preserve meaning, tone, line breaks, and formatting. "
    "Output only the translation, with no explanations."
)


class TranslationError(Exception):
    """사용자에게 그대로 보여줄 수 있는 메시지를 담은 번역 오류."""


def get_setting(name: str, default: str | None = None) -> str | None:
    """st.secrets → 환경변수(.env 포함) → 기본값 순으로 설정을 조회한다."""
    try:
        import streamlit as st

        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:  # secrets.toml이 없거나 접근 불가한 경우
        pass
    return os.getenv(name) or default


def translate(text: str, target_label: str) -> str:
    """text를 target_label(영어/일본어/중국어)로 번역해 번역문만 반환한다."""
    if target_label not in LANGUAGES:
        raise TranslationError(f"지원하지 않는 언어입니다: {target_label}")
    if not text or not text.strip():
        raise TranslationError("번역할 텍스트를 입력해주세요.")
    if len(text) > MAX_CHARS:
        raise TranslationError(f"입력은 최대 {MAX_CHARS:,}자까지 가능합니다. (현재 {len(text):,}자)")

    api_key = get_setting("OPENAI_API_KEY")
    if not api_key:
        raise TranslationError(
            "API 키가 설정되지 않았습니다. .env 파일(또는 Streamlit Secrets)에 OPENAI_API_KEY를 설정해주세요."
        )
    model = get_setting("OPENAI_MODEL", DEFAULT_MODEL)
    base_url = get_setting("OPENAI_BASE_URL")

    client = OpenAI(api_key=api_key, base_url=base_url or None, timeout=TIMEOUT_SECONDS, max_retries=0)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(target_language=LANGUAGES[target_label])},
                {"role": "user", "content": text},
            ],
        )
    except openai.AuthenticationError:
        raise TranslationError("API 키가 올바르지 않습니다. OPENAI_API_KEY를 확인해주세요.") from None
    except openai.PermissionDeniedError:
        raise TranslationError("이 API 키로는 해당 모델/기능을 사용할 권한이 없습니다.") from None
    except openai.NotFoundError:
        raise TranslationError(f"모델 '{model}'을(를) 찾을 수 없습니다. OPENAI_MODEL 설정을 확인해주세요.") from None
    except openai.RateLimitError:
        raise TranslationError("요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.") from None
    except openai.APITimeoutError:
        raise TranslationError("응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.") from None
    except openai.APIConnectionError:
        raise TranslationError("네트워크 연결에 실패했습니다. 인터넷 연결을 확인해주세요.") from None
    except openai.APIStatusError as e:
        raise TranslationError(f"번역 서버 오류가 발생했습니다. (상태 코드 {e.status_code})") from None
    except openai.OpenAIError:
        raise TranslationError("번역 중 알 수 없는 오류가 발생했습니다.") from None

    content = response.choices[0].message.content if response.choices else None
    if not content or not content.strip():
        raise TranslationError("번역 결과가 비어 있습니다. 다시 시도해주세요.")
    return content.strip()

# clients/openai_client.py
import openai
from app.core.config import settings
from app.core.logging import logger

openai.api_key = settings.OPENAI_API_KEY

def chat_completion(
    messages,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.3,
    max_tokens: int = 512,
    **kwargs,
):
    """
    공통 OpenAI ChatCompletion 래퍼
    - 환경변수/키 주입은 settings 한 곳에서만
    - 기본 파라미터 통일(temperature, max_tokens)
    """
    try:
        return openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
    except Exception as e:
        # 필요 시 로거로 교체
        logger.info(f"OpenAI API error: {e}")
        raise

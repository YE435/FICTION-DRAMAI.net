# core/config.py # 환경 변수, 키 파일 로드 중앙화
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings
from pydantic.config import ConfigDict
from app.core.paths import BASE_DIR
from app.core.logging import logger

# ------------------------------------------------------------
# .env 파일 로드
# ------------------------------------------------------------
load_dotenv(BASE_DIR / ".env")

# ------------------------------------------------------------
# 키 파일 경로 보정 유틸 함수
# ------------------------------------------------------------
def resolve_key_path(env_key_name: str, default_filename: str) -> Path:
    """
    .env에 지정된 키 경로가 상대경로일 경우 BASE_DIR 기준 절대경로로 변환합니다.
    """
    raw_value = os.getenv(env_key_name, default_filename)
    expanded = os.path.expandvars(os.path.expanduser(raw_value))  # ~, ${HOME} 처리
    key_path = Path(expanded)
    if not key_path.is_absolute():
        key_path = (BASE_DIR / key_path).resolve()
    return key_path


# ------------------------------------------------------------
# Settings 클래스 정의 (Pydantic v2 스타일)
# ------------------------------------------------------------
class Settings(BaseSettings):
    model_config = ConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    # Qdrant
    QDRANT_URL: str
    # QDRANT_API_KEY: str # qdrant 배포 후 .env 등록

    # OpenAI
    OPENAI_API_KEY: str

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str

    # JWT 관련 (RS256만 사용)
    JWT_PRIVATE_KEY: str | None = None
    JWT_PUBLIC_KEY: str | None = None
    JWT_PRIVATE_KEY_PATH: Path = Field(default_factory=lambda: resolve_key_path("JWT_PRIVATE_KEY_PATH", "private.key"))
    JWT_PUBLIC_KEY_PATH: Path = Field(default_factory=lambda: resolve_key_path("JWT_PUBLIC_KEY_PATH", "public.key"))
    JWT_ALGORITHM: str = "RS256"
    JWT_PRIVATE_KEY_PASSWORD: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --------------------------------------------------------
    # field_validator: Pydantic v2 방식
    # --------------------------------------------------------
    @model_validator(mode="after")
    def load_keys(self):
        # PRIVATE
        if self.JWT_PRIVATE_KEY_PATH and not self.JWT_PRIVATE_KEY:
            try:
                with open(self.JWT_PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
                    self.JWT_PRIVATE_KEY = f.read()
                logger.info(f"✅ PRIVATE_KEY loaded from: {self.JWT_PRIVATE_KEY_PATH}")
            except FileNotFoundError:
                raise ValueError(f"❌ PRIVATE_KEY 파일을 찾을 수 없습니다: {self.JWT_PRIVATE_KEY_PATH}")

        # PUBLIC
        if self.JWT_PUBLIC_KEY_PATH and not self.JWT_PUBLIC_KEY:
            try:
                with open(self.JWT_PUBLIC_KEY_PATH, "r", encoding="utf-8") as f:
                    self.JWT_PUBLIC_KEY = f.read()
                logger.info(f"✅ PUBLIC_KEY loaded from: {self.JWT_PUBLIC_KEY_PATH}")
            except FileNotFoundError:
                raise ValueError(f"❌ PUBLIC_KEY 파일을 찾을 수 없습니다: {self.JWT_PUBLIC_KEY_PATH}")

        return self

# ------------------------------------------------------------
# Settings 인스턴스 생성 — 실제 로드 시점
# ------------------------------------------------------------
settings = Settings()
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str = "sqlite:///./curricula_dev.db"
    groq_api_key: str = Field(default="", validation_alias=AliasChoices("GROQ_API_KEY", "GEMINI_API_KEY"))
    jwt_secret_key: str = "dev_change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    media_root: str = "storage"
    teacher_email: str = "teacher@curricula.ai"
    teacher_password: str = "Teacher@12345"
    frontend_origin: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

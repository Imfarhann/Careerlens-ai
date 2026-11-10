from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "CareerLens AI"
    environment: str = "development"
    api_prefix: str = ""

    database_url: str = (
        "postgresql+psycopg://careerlens:careerlens@localhost:5432/careerlens"
    )

    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    bcrypt_rounds: int = 12

    cors_origins: list[str] = ["http://localhost:5173"]

    upload_dir: str = "uploads"
    max_upload_size: int = 5 * 1024 * 1024

    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_timeout_seconds: float = 20.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

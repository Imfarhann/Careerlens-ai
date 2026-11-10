from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

WEAK_JWT_SECRETS = {
    "dev-only-insecure-secret-change-me",
    "ganti-dengan-string-acak-panjang",
    "change-me",
    "changeme",
    "secret",
    "your-secret-key",
}
PRODUCTION_ENVIRONMENTS = {"production", "prod"}
MIN_PRODUCTION_SECRET_LENGTH = 32


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
    rate_limit_per_minute: int = 10

    cors_origins: list[str] = ["http://localhost:5173"]

    upload_dir: str = "uploads"
    max_upload_size: int = 5 * 1024 * 1024

    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_timeout_seconds: float = 20.0

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in PRODUCTION_ENVIRONMENTS

    def validate_runtime(self) -> None:
        if not self.is_production:
            return

        secret = self.jwt_secret.strip()
        if (
            secret in WEAK_JWT_SECRETS
            or len(secret) < MIN_PRODUCTION_SECRET_LENGTH
        ):
            raise RuntimeError(
                "JWT_SECRET wajib diganti dengan nilai acak minimal "
                f"{MIN_PRODUCTION_SECRET_LENGTH} karakter saat "
                "ENVIRONMENT=production."
            )

        if "*" in self.cors_origins:
            raise RuntimeError(
                "CORS_ORIGINS tidak boleh berisi '*' saat production."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

import pytest

from app.core.config import Settings


def _settings(**overrides) -> Settings:
    values = {
        "environment": "production",
        "jwt_secret": "x" * 48,
        "cors_origins": ["https://careerlens.example"],
    }
    values.update(overrides)
    return Settings(**values)


def test_production_rejects_default_jwt_secret():
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        _settings(jwt_secret="dev-only-insecure-secret-change-me").validate_runtime()


def test_production_rejects_short_jwt_secret():
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        _settings(jwt_secret="pendek").validate_runtime()


def test_production_rejects_wildcard_cors():
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        _settings(cors_origins=["*"]).validate_runtime()


def test_production_accepts_strong_configuration():
    _settings().validate_runtime()


def test_development_allows_default_secret():
    _settings(
        environment="development",
        jwt_secret="dev-only-insecure-secret-change-me",
    ).validate_runtime()

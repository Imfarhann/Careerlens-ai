import pytest

from app.core.config import settings
from app.core.rate_limit import limiter


@pytest.fixture(autouse=True)
def limited(monkeypatch):
    limiter.reset()
    monkeypatch.setattr(settings, "rate_limit_per_minute", 3)
    yield
    limiter.reset()


def test_login_is_rate_limited(client):
    for _ in range(3):
        response = client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "salah123"},
        )
        assert response.status_code == 401

    blocked = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "salah123"},
    )

    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"] == "60"


def test_register_is_rate_limited(client):
    for index in range(3):
        response = client.post(
            "/auth/register",
            json={
                "email": f"user{index}@example.com",
                "password": "rahasia123",
            },
        )
        assert response.status_code == 201

    blocked = client.post(
        "/auth/register",
        json={"email": "user9@example.com", "password": "rahasia123"},
    )

    assert blocked.status_code == 429

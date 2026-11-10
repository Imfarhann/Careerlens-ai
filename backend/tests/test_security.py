import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_is_not_plaintext_and_uses_salt():
    first = hash_password("rahasia123")
    second = hash_password("rahasia123")

    assert first != "rahasia123"
    assert first != second


def test_verify_password_accepts_correct_password():
    hashed = hash_password("rahasia123")

    assert verify_password("rahasia123", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("rahasia123")

    assert verify_password("salah", hashed) is False


def test_verify_password_handles_malformed_hash():
    assert verify_password("rahasia123", "bukan-hash") is False


def test_hash_supports_long_passwords():
    password = "a" * 200

    assert verify_password(password, hash_password(password)) is True


def test_access_token_roundtrip():
    token = create_access_token(subject="user-123")

    assert decode_access_token(token)["sub"] == "user-123"


def test_expired_token_is_rejected():
    token = create_access_token(subject="user-123", expires_minutes=-1)

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)


def test_tampered_token_is_rejected():
    token = create_access_token(subject="user-123")
    tampered = f"{token[:-1]}x"

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered)

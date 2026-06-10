"""Authentication helpers — password hashing and JWT round-trips."""
from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError, jwt

from app.core.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import settings


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def test_hash_password_is_not_plaintext():
    hashed = hash_password("hunter2")
    assert hashed != "hunter2"
    assert len(hashed) > 20


def test_hash_password_different_each_time():
    h1 = hash_password("same-password")
    h2 = hash_password("same-password")
    assert h1 != h2  # bcrypt salts are unique per call


def test_verify_password_correct():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_empty_string():
    hashed = hash_password("non-empty")
    assert verify_password("", hashed) is False


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

def test_create_access_token_returns_string():
    token = create_access_token("user-uuid-123")
    assert isinstance(token, str)
    assert len(token) > 20


def test_decode_token_round_trip():
    subject = "11111111-1111-1111-1111-111111111111"
    token = create_access_token(subject)
    payload = decode_token(token)
    assert payload["sub"] == subject


def test_token_includes_extra_claims():
    token = create_access_token("user-id", extra={"role": "admin"})
    payload = decode_token(token)
    assert payload["role"] == "admin"


def test_token_has_expiry():
    token = create_access_token("user-id")
    payload = decode_token(token)
    assert "exp" in payload
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    assert exp > datetime.now(timezone.utc)


def test_expired_token_raises():
    # Craft an already-expired token by encoding directly with a past exp.
    past_exp = datetime.now(timezone.utc) - timedelta(seconds=1)
    expired_payload = {"sub": "user-id", "exp": past_exp}
    token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(JWTError):
        decode_token(token)


def test_tampered_token_raises():
    token = create_access_token("user-id")
    tampered = token[:-4] + "XXXX"
    with pytest.raises(JWTError):
        decode_token(tampered)


def test_wrong_secret_raises():
    payload = {"sub": "user-id", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    token = jwt.encode(payload, "wrong-secret", algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(JWTError):
        decode_token(token)

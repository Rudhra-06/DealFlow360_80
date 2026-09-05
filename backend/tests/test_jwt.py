from datetime import timedelta
import jwt
import pytest

from app.core.config import settings
from app.core.jwt import create_access_token, decode_access_token
from app.services.exceptions import ExpiredTokenError, InvalidTokenError


def test_create_and_decode_access_token_success():
    """Verify create_access_token encodes valid claims and decode_access_token decodes payload."""
    subject_id = 42
    token = create_access_token(subject=subject_id)
    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload.sub == "42"
    assert payload.type == "access"
    assert payload.iat is not None
    assert payload.exp is not None
    assert payload.exp > payload.iat


def test_decode_access_token_expired_raises_error():
    """Verify expired access token raises ExpiredTokenError."""
    # Create token that expired 10 seconds ago
    expired_token = create_access_token(subject="user_123", expires_delta=timedelta(seconds=-10))

    with pytest.raises(ExpiredTokenError) as exc_info:
        decode_access_token(expired_token)

    assert "expired" in str(exc_info.value).lower()


def test_decode_access_token_invalid_signature_raises_error():
    """Verify token signed with a different secret key raises InvalidTokenError."""
    fake_claims = {
        "sub": "user_999",
        "type": "access",
    }
    # Encode with wrong secret
    tampered_token = jwt.encode(fake_claims, "WRONG_SECRET_KEY_FOR_TEST", algorithm="HS256")

    with pytest.raises(InvalidTokenError) as exc_info:
        decode_access_token(tampered_token)

    assert "invalid token" in str(exc_info.value).lower()


def test_decode_access_token_malformed_token_raises_error():
    """Verify malformed string raises InvalidTokenError."""
    malformed = "not-a-valid-jwt-token-string"

    with pytest.raises(InvalidTokenError) as exc_info:
        decode_access_token(malformed)

    assert "invalid token" in str(exc_info.value).lower()


def test_decode_access_token_missing_subject_or_type_raises_error():
    """Verify token missing sub or incorrect type raises InvalidTokenError."""
    claims = {
        "type": "refresh",
    }
    token = jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(InvalidTokenError) as exc_info:
        decode_access_token(token)

    assert "missing required access claims" in str(exc_info.value).lower()

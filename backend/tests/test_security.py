import sys
from pathlib import Path
import pytest

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.security import hash_password, verify_password


def test_hash_password_returns_hash_and_verifies_success():
    """Verify hash_password returns a bcrypt digest and verify_password returns True for correct password."""
    plain = "TestPassword123!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(plain, hashed) is True


def test_verify_password_wrong_password_returns_false():
    """Verify verify_password returns False for incorrect plain password."""
    plain = "TestPassword123!"
    wrong = "WrongPassword123!"
    hashed = hash_password(plain)

    assert verify_password(wrong, hashed) is False


def test_hash_password_dynamic_salting():
    """Verify bcrypt dynamic salting produces different hashes for identical passwords."""
    plain = "TestPassword123!"
    hash1 = hash_password(plain)
    hash2 = hash_password(plain)

    assert hash1 != hash2
    assert verify_password(plain, hash1) is True
    assert verify_password(plain, hash2) is True


def test_verify_password_malformed_hash_returns_false_safely():
    """Verify verify_password returns False safely when given a malformed hash."""
    assert verify_password("password", "invalid_bcrypt_hash_string") is False
    assert verify_password("password", "$2b$04$short") is False
    assert verify_password("password", "") is False


def test_hash_password_overly_long_password_raises_value_error():
    """Verify passwords exceeding 72 bytes raise ValueError."""
    long_password = "A" * 73
    with pytest.raises(ValueError, match="Password exceeds maximum allowed length"):
        hash_password(long_password)


def test_verify_password_empty_inputs_returns_false():
    """Verify verify_password handles empty strings cleanly."""
    assert verify_password("", "$2b$12$somehash") is False
    assert verify_password("password", "") is False

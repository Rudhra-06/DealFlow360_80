import bcrypt


def hash_password(plain_password: str) -> str:
    """Hashes a plain-text password using bcrypt with dynamic salting.
    
    Args:
        plain_password: Plain text password string.

    Returns:
        Decoded string containing the bcrypt salted hash digest.

    Raises:
        ValueError: If password bytes exceed bcrypt maximum limit of 72 bytes.
    """
    if not isinstance(plain_password, str):
        raise TypeError("Password must be a string")
    
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password exceeds maximum allowed length of 72 bytes")
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a stored bcrypt hash digest.
    
    Args:
        plain_password: Candidate plain text password string.
        hashed_password: Stored bcrypt hash digest string.

    Returns:
        True if the password matches the hash, False otherwise or if hash is malformed.
    """
    if not plain_password or not hashed_password:
        return False
    
    if not isinstance(plain_password, str) or not isinstance(hashed_password, str):
        return False

    # Valid bcrypt hashes start with $2b$ or $2a$ and are 60 characters long
    if not (hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$")) or len(hashed_password) < 50:
        return False

    try:
        password_bytes = plain_password.encode("utf-8")
        if len(password_bytes) > 72:
            return False
        
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except BaseException:
        # Catch all malformed bcrypt inputs and Rust PanicExceptions safely
        return False

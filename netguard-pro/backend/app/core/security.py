"""
NetGuard Pro - Security Utilities

Security functions with:
- Password hashing (bcrypt/argon2)
- JWT token creation and verification
- Token validation
- Cryptographic operations
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings


# Password hashing context
# Using bcrypt as default, argon2 available as alternative
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # OWASP recommended minimum
)


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hash to verify against
        
    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.security.access_token_expire_minutes
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.secret_key,
        algorithm=settings.security.algorithm,
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create JWT refresh token.
    
    Args:
        data: Token payload data
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(
        days=settings.security.refresh_token_expire_days
    )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.secret_key,
        algorithm=settings.security.algorithm,
    )
    
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type (access/refresh)
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm],
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            return None
        
        # Check expiration (jose does this automatically, but double-check)
        exp = payload.get("exp")
        if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
            return None
        
        return payload
        
    except JWTError:
        return None


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Token length in bytes
        
    Returns:
        Hex-encoded secure token
    """
    import secrets
    return secrets.token_hex(length)


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate password meets security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Length check
    if len(password) < settings.security.password_min_length:
        errors.append(
            f"Password must be at least {settings.security.password_min_length} characters"
        )
    
    # Uppercase check
    if settings.security.password_require_uppercase:
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
    
    # Lowercase check
    if settings.security.password_require_lowercase:
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
    
    # Digit check
    if settings.security.password_require_digits:
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
    
    # Special character check
    if settings.security.password_require_special:
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


# AES encryption utilities for sensitive data
def encrypt_data(data: str, key: Optional[str] = None) -> str:
    """
    Encrypt data using AES-256.
    
    Args:
        data: Data to encrypt
        key: Encryption key (uses SECRET_KEY if not provided)
        
    Returns:
        Base64-encoded encrypted data with IV prepended
    """
    from cryptography.fernet import Fernet
    import base64
    import hashlib
    
    # Derive key from secret
    if key is None:
        key = settings.security.secret_key
    
    # Create 32-byte key from secret
    key_bytes = hashlib.sha256(key.encode()).digest()
    key_base64 = base64.urlsafe_b64encode(key_bytes)
    
    f = Fernet(key_base64)
    encrypted = f.encrypt(data.encode())
    
    return encrypted.decode()


def decrypt_data(encrypted_data: str, key: Optional[str] = None) -> str:
    """
    Decrypt AES-256 encrypted data.
    
    Args:
        encrypted_data: Base64-encoded encrypted data
        key: Decryption key (uses SECRET_KEY if not provided)
        
    Returns:
        Decrypted data string
    """
    from cryptography.fernet import Fernet
    import base64
    import hashlib
    
    # Derive key from secret
    if key is None:
        key = settings.security.secret_key
    
    # Create 32-byte key from secret
    key_bytes = hashlib.sha256(key.encode()).digest()
    key_base64 = base64.urlsafe_b64encode(key_bytes)
    
    f = Fernet(key_base64)
    decrypted = f.decrypt(encrypted_data.encode())
    
    return decrypted.decode()

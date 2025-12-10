import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from ..core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_project_token() -> tuple[str, str]:
    """Generate a project API token and its hash.

    Returns:
        tuple: (raw_token, token_hash) where raw_token should be given to user
               and token_hash should be stored in database
    """
    # Generate a secure random token
    raw_token = secrets.token_urlsafe(32)

    # Create hash for storage
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    return raw_token, token_hash


def verify_project_token(raw_token: str, stored_hash: str) -> bool:
    """Verify a project token against its stored hash."""
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return token_hash == stored_hash

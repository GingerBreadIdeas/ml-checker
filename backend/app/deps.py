from typing import Generator, Optional, Union
from datetime import datetime

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .core.config import settings
from .core.security import ALGORITHM, verify_project_token
from .database import get_db as get_db_base
from .models import User, Project, ProjectToken, UserRole
from .schemas.user import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_db() -> Generator:
    db = next(get_db_base())
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


def get_project_from_token(
    db: Session = Depends(get_db), authorization: Optional[str] = Header(None)
) -> Project:
    """Get project from API token authentication.

    This is used for API access where clients use project-specific tokens.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>" format
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Try to find matching project token
    project_tokens = db.query(ProjectToken).filter(ProjectToken.is_active == True).all()

    for pt in project_tokens:
        if verify_project_token(token, pt.token_hash):
            # Check if token is expired
            if pt.expires_at and datetime.utcnow() > pt.expires_at:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                )

            # Update last used timestamp
            pt.last_used_at = datetime.utcnow()
            db.commit()

            return pt.project
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_or_project(
    db: Session = Depends(get_db), authorization: Optional[str] = Header(None)
) -> Union[tuple[User, None], tuple[None, Project]]:
    """Get either current user (JWT) or project (API token).

    Returns:
        tuple: (user, project) where one is None and the other is the authenticated entity
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # First try JWT (user authentication)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
        user = db.query(User).filter(User.id == token_data.sub).first()
        if user and user.is_active:
            return user, None
    except (JWTError, ValidationError):
        pass

    # Then try project token
    project_tokens = db.query(ProjectToken).filter(ProjectToken.is_active == True).all()

    for pt in project_tokens:
        if verify_project_token(token, pt.token_hash):
            if pt.expires_at and datetime.utcnow() > pt.expires_at:
                continue

            pt.last_used_at = datetime.utcnow()
            db.commit()

            return None, pt.project

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_project_access(db: Session, user: User, project_id: int) -> None:
    """Verify that a user has access to a specific project.

    Args:
        db: Database session
        user: The current user
        project_id: The project ID to check access for

    Raises:
        HTTPException: If user doesn't have access to the project
    """
    user_role = db.query(UserRole).filter(
        UserRole.user_id == user.id,
        UserRole.project_id == project_id
    ).first()

    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )

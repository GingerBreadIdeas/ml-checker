from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from ..deps import get_current_user, get_db
from ..models import User as UserModel
from ..schemas.user import Token, User, UserAPIToken, UserCreate

router = APIRouter()


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = (
        db.query(UserModel)
        .filter(UserModel.email == form_data.username)
        .first()
    )
    if not user:
        user = (
            db.query(UserModel)
            .filter(UserModel.username == form_data.username)
            .first()
        )
    if not user or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/register", response_model=User)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Register a new user
    """
    # Check if user already exists
    user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    user = (
        db.query(UserModel)
        .filter(UserModel.username == user_in.username)
        .first()
    )
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists",
        )

    # Create new user
    hashed_password = get_password_hash(user_in.password)
    db_user = UserModel(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/generate-api-token", response_model=UserAPIToken)
def generate_api_token(
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Generate a long-lived API token for the current user
    """
    # Generate a long-lived token (30 days)
    api_token_expires = timedelta(days=30)

    return {
        "access_token": create_access_token(
            current_user.id, expires_delta=api_token_expires
        ),
        "token_type": "bearer",
        "expires_in": 30 * 24 * 60 * 60,  # seconds
        "username": current_user.username,
    }


@router.get("/whoami")
def whoami(
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Returns the username of the authenticated user.
    This endpoint is designed for API usage with OAuth2 tokens.
    """
    return {"username": current_user.username}

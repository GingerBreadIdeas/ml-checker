from typing import Any, Dict

from fastapi import APIRouter, Depends

from ....models.user import User
from ...deps import get_current_user

router = APIRouter()


@router.get("/whoami", response_model=Dict[str, str])
def get_username(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Returns the username of the authenticated user.
    This endpoint is designed for API usage with OAuth2 tokens.
    """
    return {"username": current_user.username}


@router.get("/status")
def get_api_status() -> Any:
    """
    Simple endpoint to check API status.
    """
    return {"status": "operational"}
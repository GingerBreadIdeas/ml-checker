from datetime import datetime, timedelta
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.security import generate_project_token
from ..deps import get_db, get_current_user
from ..models import User, Project, ProjectToken, UserRole
from ..schemas.tokens import ProjectTokenCreate, ProjectTokenResponse, ProjectTokenList

router = APIRouter()


@router.post("/projects/tokens", response_model=ProjectTokenResponse)
def create_project_token(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    expires_days: int = None,
) -> Any:
    """
    Create a new API token for the user's project.
    """
    # Get user's project through UserRole
    user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail="User has no project")

    project = user_role.project
    if not project:
        raise HTTPException(status_code=404, detail="User has no valid project")

    # Generate token
    raw_token, token_hash = generate_project_token()

    # Set expiration if specified
    expires_at = None
    if expires_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

    # Create token record
    project_token = ProjectToken(
        project_id=project.id,
        token_hash=token_hash,
        expires_at=expires_at,
        created_by_user_id=current_user.id,
        is_active=True,
    )

    db.add(project_token)
    db.commit()
    db.refresh(project_token)

    return {
        "token": raw_token,
        "token_id": project_token.id,
        "project_id": project.id,
        "project_name": project.name,
        "expires_at": expires_at,
        "created_at": project_token.created_at,
    }


@router.get("/projects/tokens", response_model=ProjectTokenList)
def list_project_tokens(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    List all tokens for the user's project (without showing the actual token values).
    """
    # Get user's project
    user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail="User has no project")

    project = user_role.project
    if not project:
        raise HTTPException(status_code=404, detail="User has no valid project")

    # Get all tokens for this project
    tokens = (
        db.query(ProjectToken)
        .filter(ProjectToken.project_id == project.id)
        .order_by(ProjectToken.created_at.desc())
        .all()
    )

    token_list = []
    for token in tokens:
        token_list.append(
            {
                "token_id": token.id,
                "is_active": token.is_active,
                "expires_at": token.expires_at,
                "created_at": token.created_at,
                "last_used_at": token.last_used_at,
                "created_by_username": token.created_by.username,
            }
        )

    return {
        "tokens": token_list,
        "project_id": project.id,
        "project_name": project.name,
    }


@router.delete("/projects/tokens/{token_id}")
def revoke_project_token(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    token_id: int,
) -> Any:
    """
    Revoke (deactivate) a project token.
    """
    # Get user's project
    user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail="User has no project")

    project = user_role.project
    if not project:
        raise HTTPException(status_code=404, detail="User has no valid project")

    # Find the token
    token = (
        db.query(ProjectToken)
        .filter(ProjectToken.id == token_id, ProjectToken.project_id == project.id)
        .first()
    )

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Deactivate token instead of deleting it (for audit trail)
    token.is_active = False
    db.commit()

    return {"message": "Token revoked successfully"}

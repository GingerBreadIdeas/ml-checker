from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_current_active_superuser, get_current_user, get_db
from ..models import Project, User, UserRole
from ..schemas.user import User as UserSchema

router = APIRouter()


@router.get("/me", response_model=UserSchema)
def read_user_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user with default project
    """
    # Find the user's default project
    default_project = (
        db.query(Project)
        .join(UserRole)
        .filter(UserRole.user_id == current_user.id)
        .filter(Project.is_default)
        .first()
    )

    # Create response with default_project_id
    user_data = UserSchema.from_orm(current_user)
    user_data.default_project_id = (
        default_project.id if default_project else None
    )

    return user_data


@router.get("/", response_model=List[UserSchema])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve users - only for superusers
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

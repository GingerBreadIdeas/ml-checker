from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from loguru import logger
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_project_from_token
from ..models import ChatMessage, Project, User, UserRole
from ..schemas.message import ChatMessage as ChatMessageSchema
from ..schemas.message import (
    ChatMessageCreate,
    ChatMessageList,
    ChatMessageUpdate,
)
from ..tasks import process_message_metrics

router = APIRouter()

default_metrics_options = {"llama_guard": {}}


def get_project_with_access(
    db: Session,
    current_user: User,
    project_id: int | None = None,
    project_name: str | None = None,
) -> Project:
    """
    Get project by ID or name and verify user has access.
    Returns the project if user has access, raises HTTPException otherwise.
    """
    if not project_id and not project_name:
        raise HTTPException(
            status_code=400,
            detail="Either project_id or project_name must be provided",
        )

    if project_id and project_name:
        raise HTTPException(
            status_code=400,
            detail="Provide either project_id or project_name, not both",
        )

    # Find the project by ID or name and check user access
    if project_id:
        user_role = (
            db.query(UserRole)
            .filter(
                UserRole.user_id == current_user.id,
                UserRole.project_id == project_id,
            )
            .first()
        )
    else:  # project_name
        user_role = (
            db.query(UserRole)
            .join(Project)
            .filter(
                UserRole.user_id == current_user.id,
                Project.name == project_name,
            )
            .first()
        )

    if not user_role:
        raise HTTPException(
            status_code=404, detail="Project not found or access denied"
        )

    return user_role.project


async def trigger_metrics_computation(message: ChatMessage, metrics_options):
    try:
        await process_message_metrics.kiq(
            message_id=message.id,
            content=message.content,
            options=metrics_options,
        )
        logger.info(
            f"Successfully queued message {message.id} for metrics computation"
        )
    except Exception as e:
        logger.exception(
            f"Failed to queue message {message.id} "
            f"for metrics computation: {e}"
        )


@router.post("/messages", response_model=ChatMessageSchema)
async def create_message(
    *,
    db: Session = Depends(get_db),
    message_in: ChatMessageCreate,
    project: Project = Depends(get_project_from_token),
) -> Any:
    """
    Create a new chat message in a project using project API token.
    """

    message = ChatMessage(
        session_id=message_in.session_id,  # Use session_id directly
        project_id=project.id,
        content=message_in.content,
        is_prompt_injection=message_in.is_prompt_injection,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    try:
        await trigger_metrics_computation(message, default_metrics_options)
    except Exception as e:
        logger.exception(f"Failed to queue message for metrics: {e}")
        # Continue - the API should still work even if task queue fails

    finally:
        return message


@router.get("/messages", response_model=ChatMessageList)
def read_messages(
    *,
    db: Session = Depends(get_db),
    project_id: int | None = Query(
        None, description="Project ID to get messages from"
    ),
    project_name: str | None = Query(
        None, description="Project name to get messages from"
    ),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve chat messages for a specific project.
    User must have access to the project.
    Specify either project_id or project_name.
    """
    project = get_project_with_access(
        db, current_user, project_id, project_name
    )
    logger.info(f"Project: {project.id}")

    # Get all messages for this project
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.project_id == project.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    logger.info(f"{messages}")
    return {"messages": messages}


@router.get("/project-messages", response_model=ChatMessageList)
def read_messages_by_token(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    project: Project = Depends(get_project_from_token),
) -> Any:
    """
    Retrieve chat messages using project token authentication.
    """
    logger.info(f"Project: {project.id}")

    # Get all messages for this project
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.project_id == project.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    logger.info(f"{messages}")
    return {"messages": messages}


@router.delete(
    "/project-messages/{message_id}", response_model=ChatMessageSchema
)
def delete_message_by_token(
    *,
    db: Session = Depends(get_db),
    message_id: int = Path(..., ge=1),
    project: Project = Depends(get_project_from_token),
) -> Any:
    """
    Delete a chat message using project token authentication.
    """
    # Get message by ID within the project
    message = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.id == message_id, ChatMessage.project_id == project.id
        )
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()
    return message


@router.get("/messages/{message_id}", response_model=ChatMessageSchema)
def read_message(
    *,
    db: Session = Depends(get_db),
    message_id: int = Path(..., ge=1),
    project_id: int | None = Query(
        None, description="Project ID containing the message"
    ),
    project_name: str | None = Query(
        None, description="Project name containing the message"
    ),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a specific chat message by ID (must belong to user's project).
    Specify either project_id or project_name.
    """
    project = get_project_with_access(
        db, current_user, project_id, project_name
    )

    # Get message by ID within the specified project
    message = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.id == message_id, ChatMessage.project_id == project.id
        )
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.delete("/messages/{message_id}", response_model=ChatMessageSchema)
def delete_message(
    *,
    db: Session = Depends(get_db),
    message_id: int = Path(..., ge=1),
    project_id: int | None = Query(
        None, description="Project ID containing the message"
    ),
    project_name: str | None = Query(
        None, description="Project name containing the message"
    ),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a chat message.
    Specify either project_id or project_name.
    """
    project = get_project_with_access(
        db, current_user, project_id, project_name
    )

    # Get message by ID within the specified project
    message = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.id == message_id, ChatMessage.project_id == project.id
        )
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()
    return message


@router.patch("/messages/{message_id}", response_model=ChatMessageSchema)
def update_message(
    *,
    db: Session = Depends(get_db),
    message_id: int = Path(..., ge=1),
    project_id: int | None = Query(
        None, description="Project ID containing the message"
    ),
    project_name: str | None = Query(
        None, description="Project name containing the message"
    ),
    message_in: ChatMessageUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a chat message's is_prompt_injection flag.
    Specify either project_id or project_name.
    """
    project = get_project_with_access(
        db, current_user, project_id, project_name
    )

    # Get message by ID within the specified project
    message = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.id == message_id, ChatMessage.project_id == project.id
        )
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.is_prompt_injection = message_in.is_prompt_injection
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

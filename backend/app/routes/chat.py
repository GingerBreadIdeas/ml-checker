import json
import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_project_from_token
from ..kafka_producer import get_kafka_producer
from ..models import ChatMessage, Project, User, UserRole
from ..schemas.message import ChatMessage as ChatMessageSchema
from ..schemas.message import ChatMessageCreate, ChatMessageList, ChatMessageUpdate

from loguru import logger
router = APIRouter()
logger = logging.getLogger(__name__)

default_metrics_options = {"llama_guard": {}}


def trigger_metrics_computation(message: ChatMessage, metrics_options):
    producer = get_kafka_producer()
    if producer is None:
        logger.warning("Kafka is not available. Prompt check will not be processed.")

    message_data = {"id": message.id, "content": message.content, "options": metrics_options}
    producer.produce(
        "compute_message_metrics", value=json.dumps(message_data).encode("utf-8")
    )
    producer.poll(0)  # Process delivery reports
    logger.info(f"Successfully sent prompt {message.id} to Kafka for checking")


@router.post("/messages", response_model=ChatMessageSchema)
def create_message(
    *,
    db: Session = Depends(get_db),
    message_in: ChatMessageCreate,
    project: Project = Depends(get_project_from_token),
) -> Any:
    """
    Create a new chat message in a project using project API token.
    """

    message = ChatMessage(
        session_id=message_in.session_id,  # Just use the string session_id directly
        project_id=project.id,
        content=message_in.content,
        is_prompt_injection=message_in.is_prompt_injection,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    try:
        trigger_metrics_computation(message, default_metrics_options)
    except Exception as e:
        logger.exception(f"Failed to send prompt to Kafka: {e}")
        # Continue execution - the API should still work even if Kafka fails

    finally:
        return message


@router.get("/messages", response_model=ChatMessageList)
def read_messages(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve chat messages for the current user's project.
    """
    # Get user's project through UserRole, preferring default project
    user_role = (
        db.query(UserRole)
        .join(Project)
        .filter(UserRole.user_id == current_user.id)
        .filter(Project.is_default == True)
        .first()
    )

    # Fallback to any project if no default project found
    if not user_role:
        user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()

    if not user_role:
        raise HTTPException(status_code=404, detail="User has no project")

    # Get the project directly from the user role
    project = user_role.project
    logger.info(f"Project: {project.id}")
    if not project:
        raise HTTPException(
            status_code=404, detail="User has no valid project"
        )

    # Get all messages for this user's project
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.project_id == project.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    logger.info(f"{messages}")
    return {"messages": messages}


@router.get("/messages/{message_id}", response_model=ChatMessageSchema)
def read_message(
    *,
    db: Session = Depends(get_db),
    message_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a specific chat message by ID (must belong to user's project).
    """
    # Get user's project through UserRole, preferring default project
    user_role = (
        db.query(UserRole)
        .join(Project)
        .filter(UserRole.user_id == current_user.id)
        .filter(Project.is_default == True)
        .first()
    )

    # Fallback to any project if no default project found
    if not user_role:
        user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()

    if not user_role:
        raise HTTPException(status_code=404, detail="User has no project")

    # Get the project directly from the user role
    project = user_role.project
    if not project:
        raise HTTPException(
            status_code=404, detail="User has no valid project"
        )

    # Get message by ID within the user's project
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.project_id == project.id
    ).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.delete("/messages/{message_id}", response_model=ChatMessageSchema)
def delete_message(
    *,
    db: Session = Depends(get_db),
    message_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a chat message.
    """
    # Get user's project through UserRole, preferring default project
    user_role = (
        db.query(UserRole)
        .join(Project)
        .filter(UserRole.user_id == current_user.id)
        .filter(Project.is_default == True)
        .first()
    )

    # Fallback to any project if no default project found
    if not user_role:
        user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()

    if not user_role:
        raise HTTPException(status_code=404, detail="User has no project")

    # Get the project directly from the user role
    project = user_role.project
    if not project:
        raise HTTPException(
            status_code=404, detail="User has no valid project"
        )

    # Get message by ID within the user's project
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.project_id == project.id
    ).first()
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
    message_in: ChatMessageUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a chat message's is_prompt_injection flag.
    """
    # Get user's project through UserRole, preferring default project
    user_role = (
        db.query(UserRole)
        .join(Project)
        .filter(UserRole.user_id == current_user.id)
        .filter(Project.is_default == True)
        .first()
    )

    # Fallback to any project if no default project found
    if not user_role:
        user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()

    if not user_role:
        raise HTTPException(status_code=404, detail="User has no project")

    # Get the project directly from the user role
    project = user_role.project
    if not project:
        raise HTTPException(
            status_code=404, detail="User has no valid project"
        )

    # Get message by ID within the user's project
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.project_id == project.id
    ).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.is_prompt_injection = message_in.is_prompt_injection
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

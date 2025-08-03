import json
import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..kafka_producer import get_kafka_producer
from ..models import ChatMessage, Organization, Project, User, UserRole
from ..schemas.message import ChatMessage as ChatMessageSchema
from ..schemas.message import ChatMessageCreate, ChatMessageList, ChatMessageUpdate

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
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new chat message in the user's default project session.
    """
    # Get user's default organization
    user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail="User has no organization")

    # Get organization's default project
    project = (
        db.query(Project)
        .filter(
            Project.organization_id == user_role.organization_id,
            Project.name == "default",
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=404, detail="Organization has no default project"
        )

    message = ChatMessage(
        session_id=message_in.session_id,  # Just use the string session_id directly
        content=message_in.content,
        response=message_in.response,
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
    Retrieve chat messages for the current user's default organization and project.
    """
    # Get user's default organization (assuming one per user for now)
    user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail="User has no organization")

    # Get organization's default project (assuming one per organization for now)
    project = (
        db.query(Project)
        .filter(
            Project.organization_id == user_role.organization_id,
            Project.name == "default",
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=404, detail="Organization has no default project"
        )

    # Get all messages for this user (through their default project)
    # Note: For now we get all messages, but could filter by session_id if needed
    messages = (
        db.query(ChatMessage)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"messages": messages}


@router.get("/messages/{message_id}", response_model=ChatMessageSchema)
def read_message(
    *,
    db: Session = Depends(get_db),
    message_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a specific chat message by ID (must belong to user's organization/project).
    """
    # Get user's default organization
    user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail="User has no organization")

    # Get organization's default project
    project = (
        db.query(Project)
        .filter(
            Project.organization_id == user_role.organization_id,
            Project.name == "default",
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=404, detail="Organization has no default project"
        )

    # Get message by ID (basic access for now)
    message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
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
    # Get user's default organization
    user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail="User has no organization")

    # Get organization's default project
    project = (
        db.query(Project)
        .filter(
            Project.organization_id == user_role.organization_id,
            Project.name == "default",
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=404, detail="Organization has no default project"
        )

    # Get message by ID (basic access for now)
    message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
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
    # Get user's default organization
    user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail="User has no organization")

    # Get organization's default project
    project = (
        db.query(Project)
        .filter(
            Project.organization_id == user_role.organization_id,
            Project.name == "default",
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=404, detail="Organization has no default project"
        )

    # Get message by ID (basic access for now)
    message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.is_prompt_injection = message_in.is_prompt_injection
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from ....db.database import get_db
from ....models.message import ChatMessage
from ....schemas.message import ChatMessage as ChatMessageSchema
from ....schemas.message import ChatMessageCreate, ChatMessageUpdate, ChatMessageList
from ...deps import get_current_user
from ....models.user import User

router = APIRouter()


@router.post("/messages", response_model=ChatMessageSchema)
def create_message(
    *,
    db: Session = Depends(get_db),
    message_in: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new chat message.
    """
    message = ChatMessage(
        user_id=current_user.id,
        content=message_in.content,
        response=message_in.response,
        is_prompt_injection=message_in.is_prompt_injection,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
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
    Retrieve chat messages for the current user.
    """
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
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
    Get a specific chat message by ID.
    """
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_id, ChatMessage.user_id == current_user.id
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
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_id, ChatMessage.user_id == current_user.id
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
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_id, ChatMessage.user_id == current_user.id
    ).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.is_prompt_injection = message_in.is_prompt_injection
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
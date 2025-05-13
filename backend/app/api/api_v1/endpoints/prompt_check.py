#!/usr/bin/env python

from typing import Any, List, Optional
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from ....db.database import get_db
from ...deps import get_current_user
from ....models.prompt import Prompt
from ....models.user import User

router = APIRouter()

from pydantic import BaseModel
class PromptCheckMessageIn(BaseModel):
    prompt_text: str
    prompt_model: str

class Prompt:



@router.post("/prompt_check")
def prompt_check(
    *,
    db: Session = Depends(get_db),
    message_in: PromptCheckMessageIn,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new chat message.
    """
    message = Prompt(
        user_id=current_user.id,
        content=dict(message_in),
        is_prompt_injection=message_in.is_prompt_injection,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    producer = get_kafka_producer()
    producer.produce("prompt_check", value=message_in.json())
    producer.poll(0)  # Process delivery reports

    return message op op

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ChatMessageBase(BaseModel):
    is_prompt_injection: Optional[bool] = False
    content: str
    session_id: Optional[str] = None


class ChatMessageCreate(ChatMessageBase):
    # project_id is determined by the API token, not from request body
    pass


class ChatMessageUpdate(BaseModel):
    is_prompt_injection: bool


class ChatMessage(BaseModel):
    id: int
    content: str
    session_id: Optional[str] = None
    project_id: int
    created_at: datetime
    response: Optional[str] = None
    is_prompt_injection: bool = False

    class Config:
        orm_mode = True


class ChatMessageList(BaseModel):
    messages: List[ChatMessage]

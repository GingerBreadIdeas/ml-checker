from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class ChatMessageBase(BaseModel):
    is_prompt_injection: Optional[bool] = False
    content: str
    session_id: str

class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageUpdate(BaseModel):
    is_prompt_injection: bool


class ChatMessage(ChatMessageBase):
    id: int
    created_at: datetime
    response: Optional[str] = None
    is_prompt_injection: bool = False

    class Config:
        orm_mode = True


class ChatMessageList(BaseModel):
    messages: List[ChatMessage]

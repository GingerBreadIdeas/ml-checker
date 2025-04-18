from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class ChatMessageBase(BaseModel):
    content: str


class ChatMessageCreate(ChatMessageBase):
    response: Optional[str] = None
    is_prompt_injection: Optional[bool] = False


class ChatMessageUpdate(BaseModel):
    is_prompt_injection: bool


class ChatMessageInDBBase(ChatMessageBase):
    id: int
    user_id: int
    created_at: datetime
    response: Optional[str] = None
    is_prompt_injection: bool = False

    class Config:
        orm_mode = True


class ChatMessage(ChatMessageInDBBase):
    pass


class ChatMessageList(BaseModel):
    messages: List[ChatMessage]
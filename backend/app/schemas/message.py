from datetime import datetime

from pydantic import BaseModel


class ChatMessageBase(BaseModel):
    is_prompt_injection: bool | None = False
    content: str
    session_id: str | None = None


class ChatMessageCreate(ChatMessageBase):
    # project_id is determined by the API token, not from request body
    pass


class ChatMessageUpdate(BaseModel):
    is_prompt_injection: bool


class ChatMessage(BaseModel):
    id: int
    content: str
    session_id: str | None = None
    project_id: int
    created_at: datetime
    response: str | None = None
    is_prompt_injection: bool = False

    class Config:
        orm_mode = True


class ChatMessageList(BaseModel):
    messages: list[ChatMessage]

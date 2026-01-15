from datetime import datetime

from pydantic import BaseModel


class ProjectTokenCreate(BaseModel):
    expires_days: int | None = None


class ProjectTokenResponse(BaseModel):
    token: str
    token_id: int
    project_id: int
    project_name: str
    expires_at: datetime | None = None
    created_at: datetime


class ProjectTokenInfo(BaseModel):
    token_id: int
    is_active: bool
    expires_at: datetime | None = None
    created_at: datetime
    last_used_at: datetime | None = None
    created_by_username: str


class ProjectTokenList(BaseModel):
    tokens: list[ProjectTokenInfo]
    project_id: int
    project_name: str

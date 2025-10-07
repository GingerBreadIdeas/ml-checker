from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ProjectTokenCreate(BaseModel):
    expires_days: Optional[int] = None


class ProjectTokenResponse(BaseModel):
    token: str
    token_id: int
    project_id: int
    project_name: str
    expires_at: Optional[datetime] = None
    created_at: datetime


class ProjectTokenInfo(BaseModel):
    token_id: int
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None
    created_by_username: str


class ProjectTokenList(BaseModel):
    tokens: List[ProjectTokenInfo]
    project_id: int
    project_name: str

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    is_active: bool | None = True
    is_superuser: bool = False


class UserCreate(UserBase):
    email: EmailStr
    username: str
    password: str = Field(..., min_length=6)


class UserUpdate(UserBase):
    password: str | None = None


class UserInDBBase(UserBase):
    id: int | None = None

    class Config:
        orm_mode = True


class User(UserInDBBase):
    default_project_id: int | None = None


class UserInDB(UserInDBBase):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: int | None = None


class UserAPIToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    username: str

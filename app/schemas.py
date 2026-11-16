from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=30)
    password: str = Field(min_length=8, max_length=100)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)


class AuthorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    author: AuthorOut
    created_at: datetime
    updated_at: datetime

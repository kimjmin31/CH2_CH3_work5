from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db

router = APIRouter(tags=["auth"])


@router.post("/auth/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(data: schemas.UserCreate, db: Annotated[Session, Depends(get_db)]):
    exists = db.scalar(select(models.User).where(models.User.email == data.email))
    if exists:
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다")

    user = models.User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# Swagger의 Authorize 버튼이 form 형식으로 보내서 OAuth2PasswordRequestForm 사용
# username 칸에 이메일을 넣으면 됨
@router.post("/auth/login", response_model=schemas.Token)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    user = db.scalar(select(models.User).where(models.User.email == form.username))
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return schemas.Token(access_token=create_access_token(user.id))


@router.get("/users/me", response_model=schemas.UserOut)
def read_me(current_user: Annotated[models.User, Depends(get_current_user)]):
    return current_user

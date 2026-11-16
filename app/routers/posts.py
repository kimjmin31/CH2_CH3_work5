from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/posts", tags=["posts"])

DB = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[models.User, Depends(get_current_user)]


def get_post_or_404(db: Session, post_id: int) -> models.Post:
    post = db.get(models.Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="게시글이 없습니다")
    return post


def check_author(post: models.Post, user: models.User) -> None:
    if post.author_id != user.id:
        raise HTTPException(status_code=403, detail="작성자만 수정/삭제할 수 있습니다")


@router.get("", response_model=list[schemas.PostOut])
def list_posts(
    db: DB,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    stmt = select(models.Post).order_by(models.Post.id.desc()).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.get("/{post_id}", response_model=schemas.PostOut)
def get_post(post_id: int, db: DB):
    return get_post_or_404(db, post_id)


@router.post("", response_model=schemas.PostOut, status_code=status.HTTP_201_CREATED)
def create_post(data: schemas.PostCreate, db: DB, user: CurrentUser):
    post = models.Post(title=data.title, content=data.content, author_id=user.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.put("/{post_id}", response_model=schemas.PostOut)
def update_post(post_id: int, data: schemas.PostUpdate, db: DB, user: CurrentUser):
    post = get_post_or_404(db, post_id)
    check_author(post, user)

    # 보낸 값만 수정
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(post, key, value)
    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: DB, user: CurrentUser):
    post = get_post_or_404(db, post_id)
    check_author(post, user)
    db.delete(post)
    db.commit()

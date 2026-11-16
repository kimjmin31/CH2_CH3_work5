from fastapi import FastAPI

from app.database import Base, engine
from app.routers import posts, users

# 처음 실행할 때 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="게시판 API",
    description="회원가입/로그인(JWT) + 게시글 CRUD",
    version="1.0.0",
)

app.include_router(users.router)
app.include_router(posts.router)


@app.get("/", tags=["health"])
def root():
    return {"message": "board api running", "docs": "/docs"}

import os
import tempfile

# 테스트는 PostgreSQL 대신 임시 SQLite 파일로 돌림 (app import 전에 설정해야 함)
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def signup_and_login(email: str, password: str = "password123") -> dict:
    client.post("/auth/signup", json={"email": email, "username": email.split("@")[0], "password": password})
    res = client.post("/auth/login", data={"username": email, "password": password})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_signup_and_duplicate():
    res = client.post("/auth/signup", json={"email": "a@test.com", "username": "aa", "password": "password123"})
    assert res.status_code == 201
    assert "password" not in res.text  # 비밀번호(해시)는 응답에 안 나와야 함

    res = client.post("/auth/signup", json={"email": "a@test.com", "username": "aa", "password": "password123"})
    assert res.status_code == 409


def test_signup_validation():
    res = client.post("/auth/signup", json={"email": "not-email", "username": "a", "password": "123"})
    assert res.status_code == 422


def test_login_wrong_password():
    client.post("/auth/signup", json={"email": "b@test.com", "username": "bb", "password": "password123"})
    res = client.post("/auth/login", data={"username": "b@test.com", "password": "wrong-pass"})
    assert res.status_code == 401


def test_me_requires_token():
    assert client.get("/users/me").status_code == 401
    headers = {"Authorization": "Bearer invalid.token.value"}
    assert client.get("/users/me", headers=headers).status_code == 401


def test_post_crud_and_author_check():
    owner = signup_and_login("owner@test.com")
    other = signup_and_login("other@test.com")

    # 로그인 없이 작성 불가
    assert client.post("/posts", json={"title": "t", "content": "c"}).status_code == 401

    res = client.post("/posts", json={"title": "첫 글", "content": "내용"}, headers=owner)
    assert res.status_code == 201
    post = res.json()
    assert post["author"]["username"] == "owner"
    post_id = post["id"]

    assert client.get(f"/posts/{post_id}").json()["title"] == "첫 글"
    assert any(p["id"] == post_id for p in client.get("/posts").json())

    # 다른 사람은 수정/삭제 불가
    assert client.put(f"/posts/{post_id}", json={"title": "x"}, headers=other).status_code == 403
    assert client.delete(f"/posts/{post_id}", headers=other).status_code == 403

    # 작성자는 수정 가능 (보낸 필드만 바뀜)
    res = client.put(f"/posts/{post_id}", json={"title": "수정된 글"}, headers=owner)
    assert res.status_code == 200
    assert res.json()["title"] == "수정된 글"
    assert res.json()["content"] == "내용"

    assert client.delete(f"/posts/{post_id}", headers=owner).status_code == 204
    assert client.get(f"/posts/{post_id}").status_code == 404


def test_post_validation():
    owner = signup_and_login("valid@test.com")
    assert client.post("/posts", json={"title": "", "content": "c"}, headers=owner).status_code == 422
    assert client.get("/posts?limit=0").status_code == 422

import pytest

from tests.conftest import auth_headers


async def test_login_success(client, user):
    resp = await client.post("/auth/login", json={"email": user.email, "password": "password123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body


async def test_login_wrong_password(client, user):
    resp = await client.post("/auth/login", json={"email": user.email, "password": "wrong"})
    assert resp.status_code == 401


async def test_login_unknown_email(client):
    resp = await client.post("/auth/login", json={"email": "nobody@example.com", "password": "x"})
    assert resp.status_code == 401


async def test_me_requires_token(client):
    resp = await client.get("/auth/me")
    assert resp.status_code in (401, 403)


async def test_me_returns_current_user(client, user):
    resp = await client.get("/auth/me", headers=auth_headers(user))
    assert resp.status_code == 200
    assert resp.json()["email"] == user.email


async def test_change_password(client, user):
    from tests.conftest import auth_headers
    h = auth_headers(user)

    wrong = await client.post("/auth/change-password", headers=h,
                              json={"current_password": "not-it", "new_password": "a-new-password"})
    assert wrong.status_code == 400
    short = await client.post("/auth/change-password", headers=h,
                              json={"current_password": "password123", "new_password": "short"})
    assert short.status_code == 422
    same = await client.post("/auth/change-password", headers=h,
                             json={"current_password": "password123", "new_password": "password123"})
    assert same.status_code == 400

    ok = await client.post("/auth/change-password", headers=h,
                           json={"current_password": "password123", "new_password": "a-new-password"})
    assert ok.status_code == 204
    assert (await client.post("/auth/login", json={"email": user.email, "password": "password123"})).status_code == 401
    assert (await client.post("/auth/login", json={"email": "learner@example.com", "password": "a-new-password"})).status_code == 200


async def test_change_password_needs_sign_in(client):
    r = await client.post("/auth/change-password", json={"current_password": "x", "new_password": "a-new-password"})
    assert r.status_code in (401, 403)

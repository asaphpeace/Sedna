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

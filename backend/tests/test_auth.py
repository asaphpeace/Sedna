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


async def _request_reset(client, email):
    """Ask for a reset link and return the token that would have been emailed."""
    from unittest.mock import AsyncMock, patch
    with patch("app.routers.auth.send_password_reset_email", new=AsyncMock()) as sent:
        resp = await client.post("/auth/forgot-password", json={"email": email})
    assert resp.status_code == 202
    return sent.await_args.args[2] if sent.await_args else None


async def test_forgot_password_resets_and_signs_in(client, user):
    token = await _request_reset(client, user.email.upper())
    assert token
    assert (await client.get(f"/auth/reset-password/{token}")).status_code == 204

    short = await client.post("/auth/reset-password", json={"token": token, "password": "short"})
    assert short.status_code == 422

    done = await client.post("/auth/reset-password", json={"token": token, "password": "a-brand-new-one"})
    assert done.status_code == 200 and "access_token" in done.json()
    assert (await client.post("/auth/login", json={"email": user.email, "password": "a-brand-new-one"})).status_code == 200
    assert (await client.post("/auth/login", json={"email": user.email, "password": "password123"})).status_code == 401

    # The link works once
    again = await client.post("/auth/reset-password", json={"token": token, "password": "another-one-123"})
    assert again.status_code == 400


async def test_forgot_password_gives_nothing_away(client):
    # Unknown emails get the same answer and no email is sent
    assert await _request_reset(client, "nobody@example.com") is None
    assert (await client.get("/auth/reset-password/made-up-token")).status_code == 400


async def test_expired_reset_link_is_refused(client, user, db_session):
    from datetime import datetime, timedelta
    from app.models import User
    token = await _request_reset(client, user.email)
    row = await db_session.get(User, user.id)
    await db_session.refresh(row)
    row.reset_token_expires_at = datetime.utcnow() - timedelta(minutes=1)
    await db_session.commit()
    resp = await client.post("/auth/reset-password", json={"token": token, "password": "a-brand-new-one"})
    assert resp.status_code == 400

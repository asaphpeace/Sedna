from unittest.mock import AsyncMock, patch

from tests.conftest import auth_headers


async def test_invite_creates_user_and_sends_email(client, admin):
    with patch("app.routers.team.send_invite_email", new=AsyncMock()) as mock_email:
        resp = await client.post("/team/invite", headers=auth_headers(admin), json={
            "email": "newbie@example.com", "name": "New Bie", "role": "Learner",
        })
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "newbie@example.com"
    assert body["status"] == "invited"
    mock_email.assert_awaited_once()
    assert mock_email.call_args.args[0] == "newbie@example.com"


async def test_invite_fires_webhook(client, admin):
    with patch("app.routers.team.send_invite_email", new=AsyncMock()), \
         patch("app.routers.team.deliver_webhook", new=AsyncMock()) as mock_hook:
        resp = await client.post("/team/invite", headers=auth_headers(admin), json={
            "email": "hooked@example.com", "name": "Hook User", "role": "Learner",
        })
    assert resp.status_code == 200
    mock_hook.assert_awaited_once()
    assert mock_hook.call_args.args[2] == "user.invited"


async def test_non_admin_cannot_invite(client, user):
    resp = await client.post("/team/invite", headers=auth_headers(user), json={
        "email": "x@example.com", "name": "X", "role": "Learner",
    })
    assert resp.status_code == 403


async def test_list_team_includes_invited_and_active(client, user, admin):
    resp = await client.get("/team", headers=auth_headers(user))
    assert resp.status_code == 200
    emails = {u["email"] for u in resp.json()}
    assert user.email in emails
    assert admin.email in emails

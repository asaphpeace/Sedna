from unittest.mock import AsyncMock, patch

import httpx

from tests.conftest import auth_headers

_real_post = httpx.AsyncClient.post


def _spy_post_only_for(url_prefix: str):
    """Intercepts outbound POSTs to url_prefix while letting the test's own
    ASGI-transport client (which also happens to be an httpx.AsyncClient) pass
    through untouched, since both share the same underlying class/method."""
    mock = AsyncMock()

    async def _fake(self, url, *args, **kwargs):
        if isinstance(url, str) and url.startswith(url_prefix):
            return await mock(url, *args, **kwargs)
        return await _real_post(self, url, *args, **kwargs)

    return mock, _fake


async def test_non_admin_cannot_manage_webhooks(client, user):
    resp = await client.get("/webhooks", headers=auth_headers(user))
    assert resp.status_code == 403


async def test_create_webhook_rejects_unknown_event(client, admin):
    resp = await client.post("/webhooks", headers=auth_headers(admin), json={
        "url": "https://example.com/hook", "events": ["not.a.real.event"],
    })
    assert resp.status_code == 400


async def test_create_and_list_webhook(client, admin):
    headers = auth_headers(admin)
    resp = await client.post("/webhooks", headers=headers, json={
        "url": "https://example.com/hook", "events": ["module.completed", "cert.earned"],
    })
    assert resp.status_code == 200

    listed = await client.get("/webhooks", headers=headers)
    assert len(listed.json()) == 1
    assert listed.json()[0]["events"] == ["module.completed", "cert.earned"]


async def test_module_complete_actually_delivers_webhook_http_post(client, user, db_session, tier_with_modules):
    """End-to-end: register a real webhook, complete a module, confirm an HTTP POST fires."""
    # Promote user to admin via the same session the app's dependency override uses,
    # so the change is visible without hitting SQLAlchemy identity-map staleness.
    user.is_admin = True
    db_session.add(user)
    await db_session.commit()

    headers = auth_headers(user)
    create_resp = await client.post("/webhooks", headers=headers, json={
        "url": "https://example.com/hook", "events": ["module.completed"], "secret": "shh",
    })
    assert create_resp.status_code == 200, create_resp.text

    m1 = tier_with_modules.modules[0]
    mock_post, fake_post = _spy_post_only_for("https://example.com")
    with patch("httpx.AsyncClient.post", new=fake_post):
        resp = await client.post(f"/progress/modules/{m1.id}/complete", headers=headers)
    assert resp.status_code == 200
    mock_post.assert_awaited_once()
    call_args = mock_post.call_args
    assert call_args.args[0] == "https://example.com/hook"
    assert "X-Sedna-Signature" in call_args.kwargs["headers"]


async def test_webhook_not_fired_for_unsubscribed_event(client, admin, tier_with_modules):
    headers = auth_headers(admin)
    # Subscribe only to cert.earned, not module.completed
    await client.post("/webhooks", headers=headers, json={
        "url": "https://example.com/hook", "events": ["cert.earned"],
    })

    m1 = tier_with_modules.modules[0]
    mock_post, fake_post = _spy_post_only_for("https://example.com")
    with patch("httpx.AsyncClient.post", new=fake_post):
        resp = await client.post(f"/progress/modules/{m1.id}/complete", headers=headers)
    assert resp.status_code == 200
    mock_post.assert_not_awaited()


async def test_posting_comment_delivers_webhook(client, user, db_session, tier_with_modules):
    """Confirms the Slack-integration path: posting a comment fires a comment.posted webhook."""
    user.is_admin = True
    db_session.add(user)
    await db_session.commit()

    headers = auth_headers(user)
    create_resp = await client.post("/webhooks", headers=headers, json={
        "url": "https://example.com/hook", "events": ["comment.posted"],
    })
    assert create_resp.status_code == 200, create_resp.text

    m1 = tier_with_modules.modules[0]
    mock_post, fake_post = _spy_post_only_for("https://example.com")
    with patch("httpx.AsyncClient.post", new=fake_post):
        resp = await client.post(f"/social/modules/{m1.id}/comments", headers=headers, json={
            "body": "Great module, thanks!",
        })
    assert resp.status_code == 200, resp.text
    mock_post.assert_awaited_once()

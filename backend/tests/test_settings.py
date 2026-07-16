from tests.conftest import auth_headers


async def test_get_notification_settings_creates_defaults(client, user):
    resp = await client.get("/settings/notifications", headers=auth_headers(user))
    assert resp.status_code == 200
    body = resp.json()
    assert body["weekly_digest"] is True  # default per model


async def test_update_notification_settings_persists(client, user):
    headers = auth_headers(user)
    resp = await client.patch("/settings/notifications", headers=headers, json={
        "weekly_digest": False, "marketing_emails": False,
    })
    assert resp.status_code == 200
    assert resp.json()["weekly_digest"] is False
    assert resp.json()["marketing_emails"] is False

    # Confirm it actually persisted, not just echoed back
    again = await client.get("/settings/notifications", headers=headers)
    assert again.json()["weekly_digest"] is False
    assert again.json()["marketing_emails"] is False
    # Untouched fields keep their previous value
    assert again.json()["cert_reminders"] is True

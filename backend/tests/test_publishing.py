"""New paths are drafts that only Sedna admins see, until published."""
from tests.conftest import auth_headers


async def _names(client, user):
    return [p["name"] for p in (await client.get("/paths", headers=auth_headers(user))).json()]


async def test_a_path_is_private_until_published(client, admin, user):
    a = auth_headers(admin)
    path = (await client.post("/admin/paths", headers=a, json={
        "name": "Laytime basics", "audience": "customer", "products": ["vms"],
    })).json()
    assert path["is_published"] is False

    tier = (await client.post(f"/admin/paths/{path['id']}/tiers", headers=a, json={
        "label": "Foundation", "name": "Foundation", "cert_name": "Laytime basics",
    })).json()

    # Can't publish an empty path, or one of draft lessons only
    assert (await client.post(f"/admin/paths/{path['id']}/publish", headers=a, json={"published": True})).status_code == 400
    lesson = (await client.post(f"/admin/tiers/{tier['id']}/modules", headers=a, json={
        "title": "What laytime is", "module_type": "a", "rich_content": "Text", "is_placeholder": True,
    })).json()
    assert (await client.post(f"/admin/paths/{path['id']}/publish", headers=a, json={"published": True})).status_code == 400

    # The admin can open the draft; a learner and the public catalogue can't see it
    assert (await client.get(f"/paths/{path['id']}", headers=a)).status_code == 200
    await client.patch(f"/admin/modules/{lesson['id']}", headers=a, json={
        "title": "What laytime is", "module_type": "a", "rich_content": "Text", "is_placeholder": False,
    })
    assert "Laytime basics" not in await _names(client, user)
    assert (await client.get(f"/paths/{path['id']}", headers=auth_headers(user))).status_code == 404
    assert (await client.get(f"/modules/{lesson['id']}", headers=auth_headers(user))).status_code == 404
    assert "Laytime basics" not in [p["name"] for p in (await client.get("/public/catalog")).json()]

    # Published: everyone who should, sees it
    published = (await client.post(f"/admin/paths/{path['id']}/publish", headers=a, json={"published": True})).json()
    assert published["is_published"] is True and published["ready_count"] == 1
    assert "Laytime basics" in await _names(client, user)
    assert "Laytime basics" in [p["name"] for p in (await client.get("/public/catalog")).json()]

    # Editing the path's details doesn't quietly unpublish it
    edited = (await client.patch(f"/admin/paths/{path['id']}", headers=a, json={
        "name": "Laytime basics", "description": "Now with a description", "audience": "customer", "products": ["vms"],
    })).json()
    assert edited["is_published"] is True

    # Unpublish hides it again
    await client.post(f"/admin/paths/{path['id']}/publish", headers=a, json={"published": False})
    assert "Laytime basics" not in await _names(client, user)

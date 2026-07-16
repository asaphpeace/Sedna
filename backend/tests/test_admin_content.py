from tests.conftest import auth_headers


async def test_non_admin_cannot_create_path(client, user):
    resp = await client.post("/admin/paths", headers=auth_headers(user), json={
        "name": "Hacker Path",
    })
    assert resp.status_code == 403


async def test_admin_full_path_tier_module_lifecycle(client, admin):
    headers = auth_headers(admin)

    # Create path
    r = await client.post("/admin/paths", headers=headers, json={
        "name": "New Path", "description": "desc", "audience": "customer", "products": ["vms"],
    })
    assert r.status_code == 200
    path = r.json()
    assert path["name"] == "New Path"

    # Create tier
    r = await client.post(f"/admin/paths/{path['id']}/tiers", headers=headers, json={
        "label": "Foundation", "name": "New Path Foundation", "cert_name": "New Path Foundation Cert",
    })
    assert r.status_code == 200
    tier = r.json()

    # Create module with video_url
    r = await client.post(f"/admin/tiers/{tier['id']}/modules", headers=headers, json={
        "title": "Intro video",
        "module_type": "v",
        "video_url": "https://www.youtube.com/watch?v=abc12345678",
        "duration_mins": 5,
        "product": "vms",
    })
    assert r.status_code == 200
    module = r.json()
    assert module["video_url"] == "https://www.youtube.com/watch?v=abc12345678"

    # Modules list should reflect it — and the PUBLIC modules endpoint must expose video_url too
    public = await client.get(f"/modules/{module['id']}", headers=headers)
    assert public.status_code == 200
    assert public.json()["video_url"] == "https://www.youtube.com/watch?v=abc12345678"

    # Update
    r = await client.patch(f"/admin/modules/{module['id']}", headers=headers, json={"title": "Updated title"})
    assert r.status_code == 200
    assert r.json()["title"] == "Updated title"

    # Delete
    r = await client.delete(f"/admin/modules/{module['id']}", headers=headers)
    assert r.status_code == 200

    r = await client.get(f"/admin/tiers/{tier['id']}/modules", headers=headers)
    assert r.json() == []


async def test_delete_path_with_tiers_is_rejected_cleanly(client, admin, tier_with_modules):
    """A path with content must not be silently deletable — it should reject with 400, not crash with 500."""
    headers = auth_headers(admin)
    role_id = tier_with_modules.role_id
    r = await client.delete(f"/admin/paths/{role_id}", headers=headers)
    assert r.status_code == 400

    r = await client.get("/admin/paths", headers=headers)
    assert any(p["id"] == role_id for p in r.json())


async def test_delete_empty_path_succeeds(client, admin):
    headers = auth_headers(admin)
    created = await client.post("/admin/paths", headers=headers, json={"name": "Empty Path"})
    path_id = created.json()["id"]

    r = await client.delete(f"/admin/paths/{path_id}", headers=headers)
    assert r.status_code == 200

    r = await client.get("/admin/paths", headers=headers)
    assert all(p["id"] != path_id for p in r.json())

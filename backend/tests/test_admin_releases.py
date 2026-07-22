from tests.conftest import auth_headers


def _release_body():
    return {
        "product": "vms", "tag": "VMS 8.26.3", "title": "Multi-port loading fix now live",
        "description": "Voyages with three or more load ports now allocate freight correctly.",
    }


async def test_non_admin_cannot_create_release(client, user):
    resp = await client.post("/admin/releases", headers=auth_headers(user), json=_release_body())
    assert resp.status_code == 403


async def test_admin_create_list_update_delete_release(client, admin):
    headers = auth_headers(admin)

    created = await client.post("/admin/releases", headers=headers, json=_release_body())
    assert created.status_code == 200
    body = created.json()
    assert body["title"] == "Multi-port loading fix now live"
    assert body["product"] == "vms"
    release_id = body["id"]

    listed = await client.get("/admin/releases", headers=headers)
    assert listed.status_code == 200
    assert any(r["id"] == release_id for r in listed.json())

    updated = await client.patch(f"/admin/releases/{release_id}", headers=headers, json={
        **_release_body(), "title": "Updated title",
    })
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated title"

    deleted = await client.delete(f"/admin/releases/{release_id}", headers=headers)
    assert deleted.status_code == 200

    listed_again = await client.get("/admin/releases", headers=headers)
    assert all(r["id"] != release_id for r in listed_again.json())


async def test_new_release_appears_on_public_releases_endpoint(client, admin, user):
    await client.post("/admin/releases", headers=auth_headers(admin), json=_release_body())

    resp = await client.get("/releases", headers=auth_headers(user))
    assert resp.status_code == 200
    assert any(r["title"] == "Multi-port loading fix now live" for r in resp.json())

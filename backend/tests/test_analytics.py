from tests.conftest import auth_headers


async def test_org_completion_rate_ignores_placeholder_modules(
    client, admin, user, tier_with_modules, tier_with_placeholder_modules
):
    # The learner finishes one of the two real modules. The two placeholder
    # modules must not count toward the total, so the rate is 1/2, not 1/4.
    m1 = tier_with_modules.modules[0]
    await client.post(f"/progress/modules/{m1.id}/complete", headers=auth_headers(user))

    resp = await client.get("/analytics/org", headers=auth_headers(admin))
    assert resp.status_code == 200
    data = resp.json()
    assert data["org_completion_rate"] == 50
    learner = next(l for l in data["learners"] if l["user_id"] == user.id)
    assert learner["completion_rate"] == 50


async def test_placeholder_content_hidden_from_learners_not_admins(
    client, admin, user, tier_with_modules, tier_with_placeholder_modules
):
    stub = tier_with_placeholder_modules.modules[0]
    real = tier_with_modules.modules[0]
    stub_path_id = tier_with_placeholder_modules.role_id

    # Learner: no placeholder modules in browse, and direct links 404
    browse = (await client.get("/modules", headers=auth_headers(user))).json()
    ids = {m["id"] for m in browse}
    assert real.id in ids and stub.id not in ids
    assert (await client.get(f"/modules/{stub.id}", headers=auth_headers(user))).status_code == 404
    assert (await client.get(f"/paths/{stub_path_id}", headers=auth_headers(user))).status_code == 404
    my_paths = (await client.get("/progress/me/paths", headers=auth_headers(user))).json()
    assert stub_path_id not in {p["role_id"] for p in my_paths}

    # Admin: still sees and opens them for authoring
    browse_admin = (await client.get("/modules", headers=auth_headers(admin))).json()
    assert stub.id in {m["id"] for m in browse_admin}
    assert (await client.get(f"/modules/{stub.id}", headers=auth_headers(admin))).status_code == 200
    assert (await client.get(f"/paths/{stub_path_id}", headers=auth_headers(admin))).status_code == 200

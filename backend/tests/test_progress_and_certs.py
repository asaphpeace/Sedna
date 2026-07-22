from tests.conftest import auth_headers


async def test_start_module_creates_progress(client, user, tier_with_modules):
    m1 = tier_with_modules.modules[0]
    resp = await client.post(f"/progress/modules/{m1.id}/start", headers=auth_headers(user))
    assert resp.status_code == 200

    prog = await client.get("/progress/me", headers=auth_headers(user))
    rows = prog.json()
    assert any(r["module_id"] == m1.id and r["state"] == "in_progress" for r in rows)


async def test_complete_module_awards_xp_once(client, user, tier_with_modules):
    m1 = tier_with_modules.modules[0]
    headers = auth_headers(user)

    first = await client.post(f"/progress/modules/{m1.id}/complete", headers=headers)
    assert first.status_code == 200
    # module_complete (10) + first-ever streak day (5)
    assert first.json()["xp_awarded"] == 15

    # Completing again must not double-award XP
    second = await client.post(f"/progress/modules/{m1.id}/complete", headers=headers)
    assert second.status_code == 200
    assert second.json()["xp_awarded"] == 0

    me = await client.get("/gamification/me", headers=headers)
    assert me.json()["xp_total"] == 15


async def test_completing_all_tier_modules_awards_certificate(client, user, tier_with_modules):
    headers = auth_headers(user)
    m1, m2 = tier_with_modules.modules[0], tier_with_modules.modules[1]

    r1 = await client.post(f"/progress/modules/{m1.id}/complete", headers=headers)
    assert r1.json()["cert_earned"] is False

    r2 = await client.post(f"/progress/modules/{m2.id}/complete", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["cert_earned"] is True
    assert r2.json()["cert_name"] == tier_with_modules.cert_name
    assert r2.json()["cert_id"] is not None

    certs = await client.get("/certificates/me", headers=headers)
    assert certs.status_code == 200
    assert len(certs.json()) == 1


async def test_path_progress_reflects_completion(client, user, tier_with_modules):
    headers = auth_headers(user)
    m1 = tier_with_modules.modules[0]
    await client.post(f"/progress/modules/{m1.id}/complete", headers=headers)

    resp = await client.get("/progress/me/paths", headers=headers)
    assert resp.status_code == 200
    role = next(r for r in resp.json() if r["role_id"] == tier_with_modules.role_id)
    assert role["done_modules"] == 1
    assert role["total_modules"] == 2
    assert role["pct"] == 50


async def test_completing_module_creates_notification(client, user, tier_with_modules):
    headers = auth_headers(user)
    m1 = tier_with_modules.modules[0]
    await client.post(f"/progress/modules/{m1.id}/complete", headers=headers)

    resp = await client.get("/notifications", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    notif = next(n for n in body["notifications"] if n["type"] == "module_complete")
    assert m1.title in notif["title"]
    assert notif["link"] == f"/modules/{m1.id}"
    assert notif["is_read"] is False


async def test_completing_module_twice_does_not_duplicate_notification(client, user, tier_with_modules):
    headers = auth_headers(user)
    m1 = tier_with_modules.modules[0]
    await client.post(f"/progress/modules/{m1.id}/complete", headers=headers)
    await client.post(f"/progress/modules/{m1.id}/complete", headers=headers)

    resp = await client.get("/notifications", headers=headers)
    complete_notifs = [n for n in resp.json()["notifications"] if n["type"] == "module_complete"]
    assert len(complete_notifs) == 1


async def test_all_placeholder_tier_still_awards_cert_when_all_completed(client, user, tier_with_placeholder_modules):
    """A freshly-imported course (every module still a stub) must not be
    permanently uncertifiable — completing everything available should
    still earn the cert, exactly as reported: a learner finished all of
    Foundations (100% placeholder content at the time) and got no cert."""
    headers = auth_headers(user)
    m1, m2 = tier_with_placeholder_modules.modules[0], tier_with_placeholder_modules.modules[1]

    r1 = await client.post(f"/progress/modules/{m1.id}/complete", headers=headers)
    assert r1.json()["cert_earned"] is False

    r2 = await client.post(f"/progress/modules/{m2.id}/complete", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["cert_earned"] is True
    assert r2.json()["cert_name"] == tier_with_placeholder_modules.cert_name

    certs = await client.get("/certificates/me", headers=headers)
    assert len(certs.json()) == 1


async def test_mixed_tier_still_excludes_placeholders_from_requirement(client, user, db_session, tier_with_modules):
    """Sanity check the fix didn't break the normal case: a tier with a mix
    of real and placeholder modules should still only require the real ones."""
    from app.models.content import Module

    placeholder = Module(
        tier_id=tier_with_modules.id, title="Unwritten bonus module",
        module_type="a", is_placeholder=True, sort_order=99,
    )
    db_session.add(placeholder)
    await db_session.commit()

    headers = auth_headers(user)
    m1, m2 = tier_with_modules.modules[0], tier_with_modules.modules[1]
    await client.post(f"/progress/modules/{m1.id}/complete", headers=headers)
    r2 = await client.post(f"/progress/modules/{m2.id}/complete", headers=headers)

    # Cert should be earned without ever completing the placeholder module.
    assert r2.json()["cert_earned"] is True

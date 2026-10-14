"""Knowledge Base and Help Center articles: public once published, written by Sedna admins."""
from app.models import Organisation, User
from tests.conftest import auth_headers

ARTICLE = {
    "title": "Freight still pending after invoicing",
    "summary": "You've invoiced but items still show as pending.",
    "section": "help-center", "kind": "Troubleshooting", "topic": "Invoicing",
    "body": "## Check these first\n\n1. Only some lines were assembled.",
}


async def test_drafts_stay_private_until_published(client, admin):
    a = auth_headers(admin)
    created = (await client.post("/admin/articles", headers=a, json=ARTICLE)).json()
    assert created["slug"] == "freight-still-pending-after-invoicing" and created["is_published"] is False

    # Not public while a draft
    assert (await client.get("/public/articles")).json() == []
    assert (await client.get(f"/public/articles/{created['slug']}")).status_code == 404

    await client.put(f"/admin/articles/{created['id']}", headers=a, json={**ARTICLE, "is_published": True, "is_sample": True})
    listed = (await client.get("/public/articles?section=help-center")).json()
    assert [x["title"] for x in listed] == [ARTICLE["title"]] and listed[0]["is_sample"] is True
    page = (await client.get(f"/public/articles/{created['slug']}")).json()
    assert page["body"].startswith("## Check these first")

    # Search finds it by words in the body, and the other section doesn't list it
    assert len((await client.get("/public/articles?q=assembled")).json()) == 1
    assert (await client.get("/public/articles?section=knowledge-base")).json() == []


async def test_slugs_stay_unique(client, admin):
    a = auth_headers(admin)
    first = (await client.post("/admin/articles", headers=a, json=ARTICLE)).json()
    second = (await client.post("/admin/articles", headers=a, json=ARTICLE)).json()
    assert first["slug"] != second["slug"]


async def test_only_sedna_admins_can_write(client, db_session):
    org = Organisation(name="Acme Bulk", slug="acme", kind="customer")
    db_session.add(org)
    await db_session.flush()
    champion = User(org_id=org.id, email="ada@acme.example", name="Ada", initial="A", status="active", is_admin=True)
    db_session.add(champion)
    await db_session.commit()
    h = auth_headers(champion)
    assert (await client.post("/admin/articles", headers=h, json=ARTICLE)).status_code == 403
    assert (await client.get("/admin/articles", headers=h)).status_code == 403


async def test_related_path_only_shown_when_customers_can_open_it(client, admin, tier_with_modules, db_session):
    from app.models import LearningRole
    a = auth_headers(admin)
    role = await db_session.get(LearningRole, tier_with_modules.role_id)
    role_id = role.id
    body = {**ARTICLE, "is_published": True, "related_path_id": role_id}
    slug = (await client.post("/admin/articles", headers=a, json=body)).json()["slug"]
    assert (await client.get(f"/public/articles/{slug}")).json()["related_path"]["id"] == role_id

    role.audience = "internal"
    await db_session.commit()
    assert (await client.get(f"/public/articles/{slug}")).json()["related_path"] is None

"""The lesson page names its path and tier for the breadcrumb."""
from tests.conftest import auth_headers


async def test_lesson_carries_path_and_tier_names(client, user, tier_with_modules):
    module_id = tier_with_modules.modules[0].id
    data = (await client.get(f"/modules/{module_id}", headers=auth_headers(user))).json()
    assert data["path_name"] == "Test Path"
    assert data["tier_label"] == "Foundation"

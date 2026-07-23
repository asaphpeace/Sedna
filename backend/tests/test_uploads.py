import io
import os

from tests.conftest import auth_headers


def _png_bytes() -> bytes:
    # Minimal valid 1x1 PNG
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d494844520000000100000001080600000"
        "01f15c4890000000a49444154789c6360000002000100" "5b8d4e6d0000000049454e44ae426082"
    )


async def test_non_admin_cannot_upload_image(client, user):
    files = {"file": ("test.png", io.BytesIO(_png_bytes()), "image/png")}
    resp = await client.post("/uploads/image", headers=auth_headers(user), files=files)
    assert resp.status_code == 403


async def test_upload_rejects_non_image_content_type(client, admin):
    files = {"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")}
    resp = await client.post("/uploads/image", headers=auth_headers(admin), files=files)
    assert resp.status_code == 400


async def test_upload_rejects_oversized_file(client, admin):
    big = io.BytesIO(b"0" * (5 * 1024 * 1024 + 1))
    files = {"file": ("big.png", big, "image/png")}
    resp = await client.post("/uploads/image", headers=auth_headers(admin), files=files)
    assert resp.status_code == 400


async def test_successful_upload_returns_fetchable_url(client, admin):
    files = {"file": ("test.png", io.BytesIO(_png_bytes()), "image/png")}
    resp = await client.post("/uploads/image", headers=auth_headers(admin), files=files)
    assert resp.status_code == 200
    url = resp.json()["url"]
    assert url.startswith("/uploads/")

    filename = url.split("/uploads/")[1]
    fetch = await client.get(url)
    assert fetch.status_code == 200

    # cleanup
    path = os.path.join("uploads", filename)
    if os.path.exists(path):
        os.remove(path)

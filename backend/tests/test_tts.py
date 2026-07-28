from unittest.mock import patch

from app.services.tts import TTSError, _chunk_text, markdown_to_plain_text
from tests.conftest import auth_headers


# ── Pure text-processing helpers (no AWS needed) ────────────────────────
def test_markdown_to_plain_text_strips_common_syntax():
    md = (
        "## Getting started\n\n"
        "This is **bold** and *italic* and `code`.\n\n"
        "> [!TIP]\n> A helpful tip.\n\n"
        "1. First step\n2. Second step\n\n"
        "![alt text](https://example.com/img.png)\n\n"
        "[a link](https://example.com)"
    )
    out = markdown_to_plain_text(md)
    assert "##" not in out
    assert "**" not in out
    assert "[!TIP]" not in out
    assert "![" not in out
    assert "Getting started" in out
    assert "bold" in out
    assert "A helpful tip." in out
    assert "First step" in out
    assert "alt text" in out
    assert "a link" in out


def test_chunk_text_splits_on_paragraph_boundaries_under_limit():
    paragraphs = ["Paragraph one. " * 20, "Paragraph two. " * 20, "Paragraph three. " * 20]
    text = "\n\n".join(paragraphs)
    chunks = _chunk_text(text, max_chars=200)
    assert len(chunks) > 1
    assert all(len(c) <= 400 for c in chunks)  # generous margin — single paragraph may exceed max_chars alone


def test_chunk_text_returns_single_chunk_for_short_text():
    chunks = _chunk_text("Just one short paragraph.", max_chars=2800)
    assert chunks == ["Just one short paragraph."]


# ── Endpoint ──────────────────────────────────────────────────────────
async def test_non_admin_cannot_generate_audio(client, user, tier_with_modules):
    article = tier_with_modules.modules[0]
    resp = await client.post(f"/admin/modules/{article.id}/generate-audio", headers=auth_headers(user))
    assert resp.status_code == 403


async def test_generate_audio_rejects_non_article_module(client, admin, tier_with_modules):
    video_module = tier_with_modules.modules[0]  # tier_with_modules fixture uses module_type="v"
    resp = await client.post(f"/admin/modules/{video_module.id}/generate-audio", headers=auth_headers(admin))
    assert resp.status_code == 400
    assert "article" in resp.json()["detail"].lower()


async def test_generate_audio_rejects_empty_article(client, admin, tier_with_modules):
    article = tier_with_modules.modules[0]
    await client.patch(f"/admin/modules/{article.id}", headers=auth_headers(admin), json={
        "title": article.title, "module_type": "a", "rich_content": None,
    })
    resp = await client.post(f"/admin/modules/{article.id}/generate-audio", headers=auth_headers(admin))
    assert resp.status_code == 400
    assert "no content" in resp.json()["detail"].lower()


async def test_generate_audio_success_persists_url(client, admin, tier_with_modules):
    article = tier_with_modules.modules[0]
    await client.patch(f"/admin/modules/{article.id}", headers=auth_headers(admin), json={
        "title": article.title, "module_type": "a", "rich_content": "## Hello\n\nSome real content here.",
    })

    with patch("app.services.tts.synthesize_article_audio", return_value="/uploads/tts-1-abcd1234.mp3") as mock_tts:
        resp = await client.post(f"/admin/modules/{article.id}/generate-audio", headers=auth_headers(admin))
    assert resp.status_code == 200
    assert resp.json()["audio_url"] == "/uploads/tts-1-abcd1234.mp3"
    mock_tts.assert_called_once()

    check = await client.get(f"/modules/{article.id}", headers=auth_headers(admin))
    assert check.json()["audio_url"] == "/uploads/tts-1-abcd1234.mp3"


async def test_generate_audio_surfaces_polly_failure_as_502(client, admin, tier_with_modules):
    article = tier_with_modules.modules[0]
    await client.patch(f"/admin/modules/{article.id}", headers=auth_headers(admin), json={
        "title": article.title, "module_type": "a", "rich_content": "Some content.",
    })

    with patch("app.services.tts.synthesize_article_audio", side_effect=TTSError("Polly synthesis failed: boom")):
        resp = await client.post(f"/admin/modules/{article.id}/generate-audio", headers=auth_headers(admin))
    assert resp.status_code == 502

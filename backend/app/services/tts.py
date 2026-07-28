"""Text-to-speech for article modules via AWS Polly.

Runs on-demand from the admin editor (not automatically on save) since
synthesis has a real per-character cost past the free tier — an admin
explicitly clicks "Generate audio" once the article text is final, and
regenerates only if they choose to.

Auth: relies on the EC2 instance's IAM role (boto3's default credential
chain) rather than access keys in .env — see docs/DEPLOYMENT.md "Setting
up text-to-speech (AWS Polly)". Falls back to explicit AWS_ACCESS_KEY_ID /
AWS_SECRET_ACCESS_KEY env vars if boto3 finds them, which is also fine for
local dev, just not what's recommended in production.
"""
import os
import re
import uuid

from app.config import settings

UPLOAD_DIR = "uploads"
# Polly's real-time SynthesizeSpeech API caps input at 3000 billed
# characters — chunk longer articles and concatenate the resulting MP3s.
# Splitting on paragraph boundaries (not mid-sentence) keeps each chunk's
# audio sounding natural on its own.
MAX_CHUNK_CHARS = 2800


def markdown_to_plain_text(text: str) -> str:
    """Strip enough Markdown syntax that Polly reads prose, not symbols.
    Not a full parser — good enough for TTS, not for rendering."""
    t = text
    t = re.sub(r"```.*?```", "", t, flags=re.DOTALL)          # code fences
    t = re.sub(r"`([^`]+)`", r"\1", t)                          # inline code
    t = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", t)             # images -> alt text
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)              # links -> label
    t = re.sub(r"^\s*>\s*\[!(TIP|WARNING|NOTE)\]\s*", "", t, flags=re.MULTILINE)  # admonition marker
    t = re.sub(r"^\s*>\s?", "", t, flags=re.MULTILINE)          # blockquote marker
    t = re.sub(r"^#{1,6}\s*", "", t, flags=re.MULTILINE)        # heading marker
    t = re.sub(r"(\*\*|__)(.*?)\1", r"\2", t)                   # bold
    t = re.sub(r"(\*|_)(.*?)\1", r"\2", t)                      # italic
    t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.MULTILINE)      # bullet marker
    t = re.sub(r"^\s*\d+\.\s+", "", t, flags=re.MULTILINE)      # numbered list marker
    t = re.sub(r"^\s*-{3,}\s*$", "", t, flags=re.MULTILINE)     # horizontal rule
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def _chunk_text(text: str, max_chars: int) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = para
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [text[:max_chars]]


class TTSError(Exception):
    pass


def synthesize_article_audio(module_id: int, rich_content: str) -> str:
    """Generate an MP3 for an article's content and return its /uploads/ URL."""
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    plain_text = markdown_to_plain_text(rich_content)
    if not plain_text:
        raise TTSError("Article has no readable content to synthesize")

    chunks = _chunk_text(plain_text, MAX_CHUNK_CHARS)

    try:
        polly = boto3.client("polly", region_name=getattr(settings, "aws_region", "us-east-1"))
        audio_bytes = b""
        for chunk in chunks:
            response = polly.synthesize_speech(
                Text=chunk,
                OutputFormat="mp3",
                VoiceId=getattr(settings, "polly_voice_id", "Joanna"),
                Engine="neural",
            )
            audio_bytes += response["AudioStream"].read()
    except (BotoCoreError, ClientError) as e:
        raise TTSError(f"Polly synthesis failed: {e}") from e

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"tts-{module_id}-{uuid.uuid4().hex[:8]}.mp3"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(audio_bytes)

    return f"/uploads/{filename}"

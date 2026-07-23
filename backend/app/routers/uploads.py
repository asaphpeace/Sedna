"""Local-disk image upload for the article editor's "Insert image" option.

Files are stored under ./uploads (persisted via a Docker volume in
production — see docker-compose.prod.yml) and served back out via the
StaticFiles mount registered in main.py at /uploads. Since the frontend
proxies everything under /api to the backend, the browser-facing URL for
an uploaded file is /api/uploads/<filename> — no reverse-proxy config
needed beyond what already exists.
"""
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.models.user import User
from app.services.deps import admin_user

router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_DIR = "uploads"
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/image")
async def upload_image(
    file: UploadFile,
    user: User = Depends(admin_user),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, "Only JPEG, PNG, GIF, or WebP images are allowed")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Unrecognized file extension")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, "Image must be 5MB or smaller")

    filename = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(contents)

    return {"url": f"/uploads/{filename}"}

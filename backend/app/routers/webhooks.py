import hashlib
import hmac
import json
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.compliance import WebhookEndpoint
from app.models.user import User
from app.services.deps import admin_user

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

SUPPORTED_EVENTS = [
    "module.completed",
    "cert.earned",
    "quiz.passed",
    "user.invited",
    "streak.milestone",
    "badge.earned",
    "comment.posted",
]


class WebhookCreate(BaseModel):
    url: str
    secret: str | None = None
    events: list[str]
    is_active: bool = True


class WebhookUpdate(BaseModel):
    url: str | None = None
    secret: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None


@router.get("")
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    result = await db.execute(
        select(WebhookEndpoint).where(WebhookEndpoint.org_id == admin.org_id)
    )
    webhooks = result.scalars().all()
    return [
        {
            "id": w.id,
            "url": w.url,
            "events": w.events,
            "is_active": w.is_active,
            "created_at": w.created_at,
        }
        for w in webhooks
    ]


@router.post("")
async def create_webhook(
    body: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    invalid = [e for e in body.events if e not in SUPPORTED_EVENTS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown events: {invalid}")

    webhook = WebhookEndpoint(
        org_id=admin.org_id,
        url=body.url,
        secret=body.secret,
        events=body.events,
        is_active=body.is_active,
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    return {"id": webhook.id, "status": "created"}


@router.patch("/{webhook_id}")
async def update_webhook(
    webhook_id: int,
    body: WebhookUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.org_id == admin.org_id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if body.url is not None:
        webhook.url = body.url
    if body.secret is not None:
        webhook.secret = body.secret
    if body.events is not None:
        webhook.events = body.events
    if body.is_active is not None:
        webhook.is_active = body.is_active

    await db.commit()
    return {"status": "updated"}


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.org_id == admin.org_id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.delete(webhook)
    await db.commit()
    return {"status": "deleted"}


@router.get("/events")
async def list_supported_events(_: User = Depends(admin_user)):
    return SUPPORTED_EVENTS


async def deliver_webhook(
    db: AsyncSession,
    org_id: int,
    event: str,
    payload: dict,
):
    """Fire webhooks for an event. Called internally from routers."""
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.org_id == org_id,
            WebhookEndpoint.is_active == True,
        )
    )
    endpoints = result.scalars().all()

    body = json.dumps({"event": event, "timestamp": datetime.now(timezone.utc).isoformat(), "data": payload})

    async with httpx.AsyncClient(timeout=10) as client:
        for ep in endpoints:
            if event not in ep.events:
                continue
            headers = {"Content-Type": "application/json"}
            if ep.secret:
                sig = hmac.new(ep.secret.encode(), body.encode(), hashlib.sha256).hexdigest()  # type: ignore[attr-defined]
                headers["X-Sedna-Signature"] = f"sha256={sig}"
            try:
                await client.post(ep.url, content=body, headers=headers)
            except Exception:
                pass  # Fire-and-forget; add delivery log table for retry in v2

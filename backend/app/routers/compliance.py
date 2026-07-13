from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.compliance import CertExpiry
from app.models.content import Tier
from app.models.progress import Certificate
from app.models.user import User
from app.services.deps import admin_user, current_user

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/me")
async def my_compliance(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    certs_result = await db.execute(
        select(Certificate)
        .where(Certificate.user_id == user.id)
        .options(selectinload(Certificate.tier))
    )
    certs = certs_result.scalars().all()

    expiry_result = await db.execute(select(CertExpiry))
    expiry_map = {e.tier_id: e for e in expiry_result.scalars().all()}

    now = datetime.utcnow()
    status = []
    for cert in certs:
        expiry_cfg = expiry_map.get(cert.tier_id)
        if expiry_cfg:
            expires_at = cert.issued_at + timedelta(days=expiry_cfg.expires_after_days)
            days_left = (expires_at - now).days
            stat = "expired" if days_left < 0 else "expiring_soon" if days_left <= 30 else "valid"
        else:
            expires_at = None
            days_left = None
            stat = "valid"

        status.append({
            "cert_id": cert.id,
            "tier_id": cert.tier_id,
            "cert_name": cert.tier.cert_name if cert.tier else "",
            "issued_at": cert.issued_at,
            "expires_at": expires_at,
            "days_left": days_left,
            "status": stat,
            "is_mandatory": expiry_cfg.is_mandatory if expiry_cfg else False,
        })

    return status


@router.get("/org/expiring")
async def org_expiring_certs(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    expiry_result = await db.execute(select(CertExpiry))
    expiry_configs = {e.tier_id: e for e in expiry_result.scalars().all()}
    if not expiry_configs:
        return []

    certs_result = await db.execute(
        select(Certificate)
        .options(selectinload(Certificate.user), selectinload(Certificate.tier))
    )
    certs = certs_result.scalars().all()

    now = datetime.utcnow()
    expiring = []
    for cert in certs:
        if cert.user and cert.user.org_id != admin.org_id:
            continue
        expiry_cfg = expiry_configs.get(cert.tier_id)
        if not expiry_cfg:
            continue
        expires_at = cert.issued_at + timedelta(days=expiry_cfg.expires_after_days)
        days_left = (expires_at - now).days
        if days_left <= days:
            expiring.append({
                "user_id": cert.user_id,
                "user_name": cert.user.name if cert.user else "",
                "user_email": cert.user.email if cert.user else "",
                "tier_id": cert.tier_id,
                "cert_name": cert.tier.cert_name if cert.tier else "",
                "issued_at": cert.issued_at,
                "expires_at": expires_at,
                "days_left": days_left,
                "is_mandatory": expiry_cfg.is_mandatory,
            })

    expiring.sort(key=lambda x: x["days_left"])
    return expiring

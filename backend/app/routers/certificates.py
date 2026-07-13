from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.progress import Certificate
from app.models.user import User
from app.schemas.progress import CertificateOut
from app.services.deps import current_user

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.get("/me", response_model=list[CertificateOut])
async def my_certificates(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(Certificate)
        .where(Certificate.user_id == user.id)
        .options(selectinload(Certificate.tier))
        .order_by(Certificate.issued_at.desc())
    )
    certs = result.scalars().all()
    return [
        CertificateOut(
            id=c.id,
            tier_id=c.tier_id,
            tier_name=c.tier.label,
            cert_name=c.tier.cert_name,
            credential_number=c.credential_number,
            issued_at=c.issued_at,
            recipient=user.name,
        )
        for c in certs
    ]

from datetime import datetime
from typing import Optional

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CertExpiry(Base):
    """Tracks certificate expiry/re-certification requirements per tier."""
    __tablename__ = "cert_expiry"

    id: Mapped[int] = mapped_column(primary_key=True)
    tier_id: Mapped[int] = mapped_column(ForeignKey("tiers.id"), unique=True)
    expires_after_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = never
    reason: Mapped[str] = mapped_column(Text, default="")  # e.g. "EU ETS regulation updated"
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)

    tier: Mapped["Tier"] = relationship()


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organisations.id"))
    url: Mapped[str] = mapped_column(String(1000))
    secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    events: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    org: Mapped["Organisation"] = relationship()

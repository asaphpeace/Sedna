from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Assignment(Base):
    """Mandatory or recommended training pushed to a user by HR/a manager,
    as opposed to the learner self-selecting a path to browse."""

    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organisations.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    tier_id: Mapped[int] = mapped_column(ForeignKey("tiers.id"), index=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # Batches everything created by one "assign to N people" admin action —
    # lets the UI show/undo a bulk assignment as a single unit.
    batch_note: Mapped[str] = mapped_column(String(255), default="")

    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    assigned_by: Mapped["User"] = relationship(foreign_keys=[assigned_by_id])
    tier: Mapped["Tier"] = relationship()

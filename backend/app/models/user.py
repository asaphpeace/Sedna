from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="organisation")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organisations.id"), index=True)
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    initial: Mapped[str] = mapped_column(String(4))
    color: Mapped[str] = mapped_column(String(20), default="#6E2BF0")
    role: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | invited | inactive
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    invite_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    invite_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    xp_total: Mapped[int] = mapped_column(default=0)
    onboarding_complete: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    organisation: Mapped["Organisation"] = relationship(back_populates="users")
    progress: Mapped[list["UserModuleProgress"]] = relationship(back_populates="user")
    certificates: Mapped[list["Certificate"]] = relationship(back_populates="user")
    saved_modules: Mapped[list["SavedModule"]] = relationship(back_populates="user")
    activity: Mapped[list["ActivityLog"]] = relationship(back_populates="user")
    notification_settings: Mapped[Optional["NotificationSettings"]] = relationship(
        back_populates="user", uselist=False
    )

from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    weekly_digest: Mapped[bool] = mapped_column(Boolean, default=True)
    new_modules: Mapped[bool] = mapped_column(Boolean, default=True)
    cert_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    product_releases: Mapped[bool] = mapped_column(Boolean, default=True)
    team_activity: Mapped[bool] = mapped_column(Boolean, default=False)
    marketing_emails: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="notification_settings")

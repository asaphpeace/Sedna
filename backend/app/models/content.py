from typing import Optional
from sqlalchemy import ARRAY, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LearningRole(Base):
    """A learning path (e.g. 'Voyage Operator', 'Support Engineer')."""

    __tablename__ = "learning_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(100), default="ti-user")
    color: Mapped[str] = mapped_column(String(20), default="purple")
    audience: Mapped[str] = mapped_column(String(20), default="customer")  # customer | internal
    products: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    tiers: Mapped[list["Tier"]] = relationship(
        back_populates="role", order_by="Tier.sort_order"
    )


class Tier(Base):
    """A tier within a learning role (Foundation / Practitioner / Professional)."""

    __tablename__ = "tiers"

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("learning_roles.id"))
    label: Mapped[str] = mapped_column(String(50))       # Foundation | Practitioner | Professional
    name: Mapped[str] = mapped_column(String(255))        # e.g. "Voyage Operator Foundation"
    cert_name: Mapped[str] = mapped_column(String(255))   # certificate awarded
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    role: Mapped["LearningRole"] = relationship(back_populates="tiers")
    modules: Mapped[list["Module"]] = relationship(
        back_populates="tier", order_by="Module.sort_order"
    )
    certificates: Mapped[list["Certificate"]] = relationship(back_populates="tier")


class Module(Base):
    """A single learning module (video or article)."""

    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    tier_id: Mapped[int] = mapped_column(ForeignKey("tiers.id"))
    title: Mapped[str] = mapped_column(String(500))
    module_type: Mapped[str] = mapped_column(String(10), default="v")  # v | a
    duration_mins: Mapped[int] = mapped_column(Integer, default=0)
    product: Mapped[str] = mapped_column(String(20), default="vms")   # vms | stream | cross
    is_placeholder: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Rich content
    description: Mapped[str] = mapped_column(Text, default="")
    learn_items: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    rich_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON (Tiptap)
    video_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    video_duration_secs: Mapped[int] = mapped_column(Integer, default=0)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tier: Mapped["Tier"] = relationship(back_populates="modules")
    progress: Mapped[list["UserModuleProgress"]] = relationship(back_populates="module")
    saved_by: Mapped[list["SavedModule"]] = relationship(back_populates="module")

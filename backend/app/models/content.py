from datetime import datetime
from typing import Optional
from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Integer, String, Text, func
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
    # Drafts are visible only to Sedna admins, so a path can be built in private
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

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
    audio_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # generated via AWS Polly

    tier: Mapped["Tier"] = relationship(back_populates="modules")
    progress: Mapped[list["UserModuleProgress"]] = relationship(back_populates="module")
    saved_by: Mapped[list["SavedModule"]] = relationship(back_populates="module")


class Article(Base):
    """A Knowledge Base or Help Center article, public before sign-in once
    published. Knowledge Base = how-tos and explainers; Help Center =
    troubleshooting and support processes."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text, default="")        # "This is for you if…"
    section: Mapped[str] = mapped_column(String(20), default="knowledge-base")  # knowledge-base | help-center
    kind: Mapped[str] = mapped_column(String(30), default="How-to")  # How-to | Explainer | Troubleshooting | Process
    product: Mapped[str] = mapped_column(String(20), default="vms")  # vms | stream | all
    topic: Mapped[str] = mapped_column(String(80), default="")
    body: Mapped[str] = mapped_column(Text, default="")             # markdown
    related_path_id: Mapped[Optional[int]] = mapped_column(ForeignKey("learning_roles.id", ondelete="SET NULL"), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    # Drafted from support cases and awaiting review: shown with a visible label
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

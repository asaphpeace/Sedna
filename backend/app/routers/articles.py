"""Knowledge Base and Help Center articles.

Published articles are public, so people can find answers before signing in.
Only Sedna admins write and publish them.
"""
import re
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.content import Article, LearningRole
from app.models.user import User
from app.services.deps import sedna_admin_user

public_router = APIRouter(prefix="/public/articles", tags=["articles"])
admin_router = APIRouter(prefix="/admin/articles", tags=["articles"])

Section = Literal["knowledge-base", "help-center"]
Kind = Literal["How-to", "Explainer", "Troubleshooting", "Process"]
Product = Literal["vms", "stream", "all"]


class ArticleSummary(BaseModel):
    slug: str
    title: str
    summary: str
    section: str
    kind: str
    product: str
    topic: str
    is_sample: bool
    updated_at: Optional[datetime]
    model_config = {"from_attributes": True}


class ArticleOut(ArticleSummary):
    body: str
    related_path: Optional[dict] = None


class ArticleAdminOut(ArticleOut):
    id: int
    is_published: bool
    related_path_id: Optional[int]
    sort_order: int


class ArticleIn(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    slug: Optional[str] = Field(default=None, max_length=160)
    summary: str = ""
    section: Section = "knowledge-base"
    kind: Kind = "How-to"
    product: Product = "vms"
    topic: str = ""
    body: str = ""
    related_path_id: Optional[int] = None
    is_published: bool = False
    is_sample: bool = False
    sort_order: int = 0


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:160] or "article"


async def _related(db: AsyncSession, a: Article) -> Optional[dict]:
    if not a.related_path_id:
        return None
    role = await db.get(LearningRole, a.related_path_id)
    # Articles are public, so only point at a published customer path: one a
    # customer reader could actually open once signed in
    if not role or not role.is_published or role.audience != "customer":
        return None
    return {"id": role.id, "name": role.name, "audience": role.audience}


# ── Public ───────────────────────────────────────────────

@public_router.get("", response_model=list[ArticleSummary])
async def list_articles(
    section: Optional[Section] = None,
    product: Optional[Product] = None,
    q: Optional[str] = Query(None, max_length=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Article).where(Article.is_published == True)
    if section:
        stmt = stmt.where(Article.section == section)
    if product:
        stmt = stmt.where(Article.product.in_((product, "all")))
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Article.title.ilike(like), Article.summary.ilike(like),
                              Article.topic.ilike(like), Article.body.ilike(like)))
    stmt = stmt.order_by(Article.sort_order, Article.title)
    return (await db.execute(stmt)).scalars().all()


@public_router.get("/{slug}", response_model=ArticleOut)
async def get_article(slug: str, db: AsyncSession = Depends(get_db)):
    a = (await db.execute(
        select(Article).where(Article.slug == slug, Article.is_published == True)
    )).scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    out = ArticleOut.model_validate(a)
    out.related_path = await _related(db, a)
    return out


# ── Admin (Sedna admins) ─────────────────────────────────

@admin_router.get("", response_model=list[ArticleAdminOut])
async def admin_list(db: AsyncSession = Depends(get_db), _: User = Depends(sedna_admin_user)):
    return (await db.execute(select(Article).order_by(Article.section, Article.sort_order, Article.title))).scalars().all()


async def _unique_slug(db: AsyncSession, wanted: str, own_id: Optional[int] = None) -> str:
    base, slug, n = wanted, wanted, 2
    while True:
        clash = await db.scalar(select(Article.id).where(Article.slug == slug))
        if not clash or clash == own_id:
            return slug
        slug, n = f"{base}-{n}", n + 1


@admin_router.post("", response_model=ArticleAdminOut)
async def admin_create(body: ArticleIn, db: AsyncSession = Depends(get_db), _: User = Depends(sedna_admin_user)):
    data = body.model_dump()
    data["slug"] = await _unique_slug(db, _slugify(body.slug or body.title))
    a = Article(**data)
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a


@admin_router.put("/{article_id}", response_model=ArticleAdminOut)
async def admin_update(article_id: int, body: ArticleIn, db: AsyncSession = Depends(get_db),
                       _: User = Depends(sedna_admin_user)):
    a = await db.get(Article, article_id)
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    data = body.model_dump()
    data["slug"] = await _unique_slug(db, _slugify(body.slug or body.title), own_id=a.id)
    for k, v in data.items():
        setattr(a, k, v)
    await db.commit()
    await db.refresh(a)
    return a


@admin_router.delete("/{article_id}", status_code=204)
async def admin_delete(article_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(sedna_admin_user)):
    a = await db.get(Article, article_id)
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    await db.delete(a)
    await db.commit()

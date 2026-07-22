from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.content import Module
from app.models.social import CommentLike, ModuleComment
from app.models.user import User
from app.services.deps import current_user
from app.routers.webhooks import deliver_webhook

router = APIRouter(prefix="/social", tags=["social"])


class CreateComment(BaseModel):
    body: str
    parent_id: int | None = None


@router.get("/modules/{module_id}/comments")
async def get_comments(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(ModuleComment)
        .where(ModuleComment.module_id == module_id, ModuleComment.parent_id == None)
        .options(selectinload(ModuleComment.replies).selectinload(ModuleComment.author))
        .options(selectinload(ModuleComment.author))
        .order_by(ModuleComment.created_at.desc())
    )
    comments = result.scalars().all()

    # Get user's likes for this module's comments
    all_comment_ids = [c.id for c in comments] + [r.id for c in comments for r in c.replies]
    likes_result = await db.execute(
        select(CommentLike.comment_id).where(
            CommentLike.user_id == user.id,
            CommentLike.comment_id.in_(all_comment_ids),
        )
    )
    liked_ids = {row[0] for row in likes_result.all()}

    def fmt(c: ModuleComment, include_replies: bool = True):
        return {
            "id": c.id,
            "body": c.body,
            "author_name": c.author.name if c.author else "Unknown",
            "author_id": c.user_id,
            "like_count": c.like_count,
            "liked_by_me": c.id in liked_ids,
            "created_at": c.created_at,
            "replies": [fmt(r, False) for r in (c.replies if include_replies else [])],
        }

    return [fmt(c) for c in comments]


@router.post("/modules/{module_id}/comments")
async def create_comment(
    module_id: int,
    body: CreateComment,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    if len(body.body.strip()) < 2:
        raise HTTPException(status_code=400, detail="Comment too short")

    comment = ModuleComment(
        module_id=module_id,
        user_id=user.id,
        body=body.body.strip(),
        parent_id=body.parent_id,
        like_count=0,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    mod_result = await db.execute(select(Module).where(Module.id == module_id))
    module = mod_result.scalar_one_or_none()
    await deliver_webhook(db, user.org_id, "comment.posted", {
        "user_id": user.id, "user_name": user.name,
        "module_id": module_id, "module_title": module.title if module else None,
        "comment_id": comment.id, "body": comment.body,
        "is_reply": comment.parent_id is not None,
    })

    return {"id": comment.id, "status": "ok"}


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(ModuleComment).where(ModuleComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not your comment")
    await db.delete(comment)
    await db.commit()
    return {"status": "ok"}


@router.post("/comments/{comment_id}/like")
async def toggle_like(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    existing = await db.execute(
        select(CommentLike).where(
            CommentLike.user_id == user.id,
            CommentLike.comment_id == comment_id,
        )
    )
    like = existing.scalar_one_or_none()

    comment_result = await db.execute(
        select(ModuleComment).where(ModuleComment.id == comment_id)
    )
    comment = comment_result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if like:
        await db.delete(like)
        comment.like_count = max(0, comment.like_count - 1)
        liked = False
    else:
        db.add(CommentLike(user_id=user.id, comment_id=comment_id))
        comment.like_count += 1
        liked = True

    await db.commit()
    return {"liked": liked, "like_count": comment.like_count}

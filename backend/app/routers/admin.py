"""Admin CRUD: paths (learning roles), tiers, modules."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.content import LearningRole, Module, Tier
from app.models.progress import SavedModule, UserModuleProgress
from app.models.quiz import QuizAttempt, QuizOption, QuizQuestion
from app.models.release import Release
from app.models.social import ModuleComment
from app.models.user import User
from app.services.deps import current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return user


# ── Schemas ────────────────────────────────────────────────────────────────

class PathIn(BaseModel):
    name: str
    description: str = ""
    icon: str = "ti-user"
    color: str = "purple"
    audience: str = "customer"
    products: list[str] = []
    sort_order: int = 0


class TierIn(BaseModel):
    label: str
    name: str
    cert_name: str
    sort_order: int = 0


class ModuleIn(BaseModel):
    title: str
    module_type: str = "v"          # v | a | l  (video / article / link)
    duration_mins: int = 0
    product: str = "vms"
    is_placeholder: bool = False
    sort_order: int = 0
    description: str = ""
    learn_items: list[str] = []
    video_url: Optional[str] = None
    transcript: Optional[str] = None
    rich_content: Optional[str] = None  # markdown / plain text


class PathOut(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    color: str
    audience: str
    products: list[str]
    sort_order: int
    tier_count: int
    mod_count: int
    model_config = {"from_attributes": True}


class TierOut(BaseModel):
    id: int
    role_id: int
    label: str
    name: str
    cert_name: str
    sort_order: int
    mod_count: int
    model_config = {"from_attributes": True}


class ModuleOut(BaseModel):
    id: int
    tier_id: int
    title: str
    module_type: str
    duration_mins: int
    product: str
    is_placeholder: bool
    sort_order: int
    description: str
    learn_items: list[str]
    video_url: Optional[str]
    transcript: Optional[str]
    rich_content: Optional[str]
    model_config = {"from_attributes": True}


class QuizOptionIn(BaseModel):
    text: str
    is_correct: bool = False


class QuizQuestionIn(BaseModel):
    question_text: str
    explanation: str = ""
    sort_order: int = 0
    options: list[QuizOptionIn] = []


class QuizOptionOut(BaseModel):
    id: int
    text: str
    is_correct: bool
    sort_order: int
    model_config = {"from_attributes": True}


class QuizQuestionOut(BaseModel):
    id: int
    module_id: Optional[int]
    tier_id: Optional[int]
    question_text: str
    explanation: str
    sort_order: int
    options: list[QuizOptionOut]
    model_config = {"from_attributes": True}


class ReleaseIn(BaseModel):
    product: str = "vms"          # vms | stream | academy
    tag: str = ""
    title: str
    description: str = ""
    published_at: Optional[datetime] = None
    module_count: int = 0


class ReleaseOut(BaseModel):
    id: int
    product: str
    tag: str
    title: str
    description: str
    published_at: datetime
    module_count: int
    model_config = {"from_attributes": True}


# ── Paths ──────────────────────────────────────────────────────────────────

@router.get("/paths", response_model=list[PathOut])
async def list_paths(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(LearningRole)
        .options(selectinload(LearningRole.tiers).selectinload(Tier.modules))
        .order_by(LearningRole.sort_order)
    )
    roles = result.scalars().all()
    out = []
    for r in roles:
        mod_count = sum(len(t.modules) for t in r.tiers)
        out.append(PathOut(
            id=r.id, name=r.name, description=r.description,
            icon=r.icon, color=r.color, audience=r.audience,
            products=r.products, sort_order=r.sort_order,
            tier_count=len(r.tiers), mod_count=mod_count,
        ))
    return out


@router.post("/paths", response_model=PathOut)
async def create_path(
    body: PathIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    role = LearningRole(**body.model_dump())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return PathOut(
        id=role.id, name=role.name, description=role.description,
        icon=role.icon, color=role.color, audience=role.audience,
        products=role.products, sort_order=role.sort_order,
        tier_count=0, mod_count=0,
    )


@router.patch("/paths/{path_id}", response_model=PathOut)
async def update_path(
    path_id: int,
    body: PathIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(LearningRole)
        .where(LearningRole.id == path_id)
        .options(selectinload(LearningRole.tiers).selectinload(Tier.modules))
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(404, "Path not found")
    for k, v in body.model_dump().items():
        setattr(role, k, v)
    await db.commit()
    await db.refresh(role)
    mod_count = sum(len(t.modules) for t in role.tiers)
    return PathOut(
        id=role.id, name=role.name, description=role.description,
        icon=role.icon, color=role.color, audience=role.audience,
        products=role.products, sort_order=role.sort_order,
        tier_count=len(role.tiers), mod_count=mod_count,
    )


@router.delete("/paths/{path_id}")
async def delete_path(
    path_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(LearningRole).where(LearningRole.id == path_id).options(selectinload(LearningRole.tiers))
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(404, "Path not found")
    if role.tiers:
        raise HTTPException(400, "Delete all tiers in this path before deleting the path itself")
    await db.delete(role)
    await db.commit()
    return {"status": "deleted"}


# ── Tiers ──────────────────────────────────────────────────────────────────

@router.get("/paths/{path_id}/tiers", response_model=list[TierOut])
async def list_tiers(
    path_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(Tier)
        .where(Tier.role_id == path_id)
        .options(selectinload(Tier.modules))
        .order_by(Tier.sort_order)
    )
    tiers = result.scalars().all()
    return [TierOut(
        id=t.id, role_id=t.role_id, label=t.label, name=t.name,
        cert_name=t.cert_name, sort_order=t.sort_order, mod_count=len(t.modules)
    ) for t in tiers]


@router.post("/paths/{path_id}/tiers", response_model=TierOut)
async def create_tier(
    path_id: int,
    body: TierIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    tier = Tier(role_id=path_id, **body.model_dump())
    db.add(tier)
    await db.commit()
    await db.refresh(tier)
    return TierOut(id=tier.id, role_id=tier.role_id, label=tier.label,
                   name=tier.name, cert_name=tier.cert_name,
                   sort_order=tier.sort_order, mod_count=0)


@router.patch("/tiers/{tier_id}", response_model=TierOut)
async def update_tier(
    tier_id: int,
    body: TierIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(Tier).where(Tier.id == tier_id).options(selectinload(Tier.modules))
    )
    tier = result.scalar_one_or_none()
    if not tier:
        raise HTTPException(404, "Tier not found")
    for k, v in body.model_dump().items():
        setattr(tier, k, v)
    await db.commit()
    await db.refresh(tier)
    return TierOut(id=tier.id, role_id=tier.role_id, label=tier.label,
                   name=tier.name, cert_name=tier.cert_name,
                   sort_order=tier.sort_order, mod_count=len(tier.modules))


@router.delete("/tiers/{tier_id}")
async def delete_tier(
    tier_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(Tier).where(Tier.id == tier_id).options(selectinload(Tier.modules))
    )
    tier = result.scalar_one_or_none()
    if not tier:
        raise HTTPException(404, "Tier not found")
    if tier.modules:
        raise HTTPException(400, "Delete all modules in this tier before deleting the tier itself")
    await db.delete(tier)
    await db.commit()
    return {"status": "deleted"}


# ── Modules ────────────────────────────────────────────────────────────────

@router.get("/tiers/{tier_id}/modules", response_model=list[ModuleOut])
async def list_tier_modules(
    tier_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(Module).where(Module.tier_id == tier_id).order_by(Module.sort_order)
    )
    return result.scalars().all()


@router.post("/tiers/{tier_id}/modules", response_model=ModuleOut)
async def create_module(
    tier_id: int,
    body: ModuleIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    mod = Module(tier_id=tier_id, **body.model_dump())
    db.add(mod)
    await db.commit()
    await db.refresh(mod)
    return mod


@router.patch("/modules/{module_id}", response_model=ModuleOut)
async def update_module(
    module_id: int,
    body: ModuleIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(select(Module).where(Module.id == module_id))
    mod = result.scalar_one_or_none()
    if not mod:
        raise HTTPException(404, "Module not found")
    for k, v in body.model_dump().items():
        setattr(mod, k, v)
    await db.commit()
    await db.refresh(mod)
    return mod


@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(select(Module).where(Module.id == module_id))
    mod = result.scalar_one_or_none()
    if not mod:
        raise HTTPException(404, "Module not found")

    # Real learner activity blocks deletion outright — checked explicitly,
    # per table, so the error actually reflects what's blocking it.
    if (await db.execute(
        select(UserModuleProgress.id).where(UserModuleProgress.module_id == module_id).limit(1)
    )).scalar_one_or_none():
        raise HTTPException(400, "Cannot delete: learners have progress recorded against this module")

    if (await db.execute(
        select(QuizAttempt.id).where(QuizAttempt.module_id == module_id).limit(1)
    )).scalar_one_or_none():
        raise HTTPException(400, "Cannot delete: learners have quiz attempts recorded against this module")

    if (await db.execute(
        select(SavedModule.id).where(SavedModule.module_id == module_id).limit(1)
    )).scalar_one_or_none():
        raise HTTPException(400, "Cannot delete: learners have saved this module")

    if (await db.execute(
        select(ModuleComment.id).where(ModuleComment.module_id == module_id).limit(1)
    )).scalar_one_or_none():
        raise HTTPException(400, "Cannot delete: this module has learner comments")

    # No real learner activity — safe to remove any never-attempted quiz
    # content attached to this module first (QuizOption rows cascade via
    # the existing relationship), since QuizQuestion.module_id has no
    # ON DELETE CASCADE at the database level and would otherwise block
    # deletion of the module itself even though nobody ever answered it.
    quiz_result = await db.execute(select(QuizQuestion).where(QuizQuestion.module_id == module_id))
    for question in quiz_result.scalars().all():
        await db.delete(question)

    try:
        await db.delete(mod)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Cannot delete: this module is still referenced elsewhere")
    return {"status": "deleted"}


# ── Quiz authoring ───────────────────────────────────────────────────────────
# Unlike the learner-facing endpoints in routers/quizzes.py (which strip
# is_correct from every option), these expose the correct answer — an admin
# needs to see and set it.

def _validate_options(options: list[QuizOptionIn]) -> None:
    if len(options) < 2:
        raise HTTPException(400, "A question needs at least 2 options")
    if sum(1 for o in options if o.is_correct) != 1:
        raise HTTPException(400, "Exactly one option must be marked correct")


@router.get("/modules/{module_id}/quiz", response_model=list[QuizQuestionOut])
async def list_module_quiz(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.module_id == module_id)
        .options(selectinload(QuizQuestion.options))
        .order_by(QuizQuestion.sort_order)
    )
    return result.scalars().all()


@router.post("/modules/{module_id}/quiz/questions", response_model=QuizQuestionOut)
async def create_quiz_question(
    module_id: int,
    body: QuizQuestionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    mod_result = await db.execute(select(Module).where(Module.id == module_id))
    if not mod_result.scalar_one_or_none():
        raise HTTPException(404, "Module not found")
    _validate_options(body.options)

    question = QuizQuestion(
        module_id=module_id,
        question_text=body.question_text,
        explanation=body.explanation,
        sort_order=body.sort_order,
        options=[QuizOption(text=o.text, is_correct=o.is_correct, sort_order=i)
                 for i, o in enumerate(body.options)],
    )
    db.add(question)
    await db.commit()
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.id == question.id).options(selectinload(QuizQuestion.options))
    )
    return result.scalar_one()


@router.patch("/quiz-questions/{question_id}", response_model=QuizQuestionOut)
async def update_quiz_question(
    question_id: int,
    body: QuizQuestionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.id == question_id).options(selectinload(QuizQuestion.options))
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(404, "Question not found")
    _validate_options(body.options)

    question.question_text = body.question_text
    question.explanation = body.explanation
    question.sort_order = body.sort_order
    # Full replace of options — simplest correct behavior for a v1 editor
    # (cascade="all, delete-orphan" on the relationship handles cleanup).
    question.options = [QuizOption(text=o.text, is_correct=o.is_correct, sort_order=i)
                         for i, o in enumerate(body.options)]
    await db.commit()
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.id == question_id).options(selectinload(QuizQuestion.options))
    )
    return result.scalar_one()


@router.delete("/quiz-questions/{question_id}")
async def delete_quiz_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(select(QuizQuestion).where(QuizQuestion.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(404, "Question not found")
    try:
        await db.delete(question)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Cannot delete: learners have already attempted this question")
    return {"status": "deleted"}


# ── Releases ("What's New") ──────────────────────────────────────────────────

@router.get("/releases", response_model=list[ReleaseOut])
async def list_releases(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(select(Release).order_by(Release.published_at.desc()))
    return result.scalars().all()


@router.post("/releases", response_model=ReleaseOut)
async def create_release(
    body: ReleaseIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    data = body.model_dump()
    if data["published_at"] is None:
        data.pop("published_at")  # let the DB default (now) apply
    release = Release(**data)
    db.add(release)
    await db.commit()
    await db.refresh(release)
    return release


@router.patch("/releases/{release_id}", response_model=ReleaseOut)
async def update_release(
    release_id: int,
    body: ReleaseIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(select(Release).where(Release.id == release_id))
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(404, "Release not found")
    for k, v in body.model_dump().items():
        if k == "published_at" and v is None:
            continue
        setattr(release, k, v)
    await db.commit()
    await db.refresh(release)
    return release


@router.delete("/releases/{release_id}")
async def delete_release(
    release_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(select(Release).where(Release.id == release_id))
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(404, "Release not found")
    await db.delete(release)
    await db.commit()
    return {"status": "deleted"}

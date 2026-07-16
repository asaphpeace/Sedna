from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.quiz import QuizAttempt, QuizAttemptAnswer, QuizOption, QuizQuestion
from app.models.user import User
from app.services.cert_award import check_and_award_cert
from app.services.deps import current_user
from app.services.gamification import award_xp, check_and_award_badges, update_streak
from app.routers.webhooks import deliver_webhook

router = APIRouter(prefix="/quizzes", tags=["quizzes"])
limiter = Limiter(key_func=get_remote_address)


class SubmitAnswer(BaseModel):
    question_id: int
    option_id: int


class SubmitAttempt(BaseModel):
    module_id: int | None = None
    tier_id: int | None = None
    answers: list[SubmitAnswer]


def _fmt_question(q: QuizQuestion) -> dict:
    return {
        "id": q.id,
        "question": q.question_text,
        "explanation": q.explanation,
        "options": [{"id": o.id, "text": o.text} for o in q.options],
    }


@router.get("/module/{module_id}")
async def get_module_quiz(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
):
    result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.module_id == module_id)
        .options(selectinload(QuizQuestion.options))
        .order_by(QuizQuestion.sort_order)
    )
    return [_fmt_question(q) for q in result.scalars().all()]


@router.get("/tier/{tier_id}")
async def get_tier_quiz(
    tier_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
):
    result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.tier_id == tier_id)
        .options(selectinload(QuizQuestion.options))
        .order_by(QuizQuestion.sort_order)
    )
    return [_fmt_question(q) for q in result.scalars().all()]


@router.post("/attempt")
@limiter.limit("30/minute")
async def submit_attempt(
    request: Request,
    body: SubmitAttempt,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    if not body.module_id and not body.tier_id:
        raise HTTPException(status_code=400, detail="module_id or tier_id required")

    filter_col = QuizQuestion.module_id if body.module_id else QuizQuestion.tier_id
    filter_val = body.module_id or body.tier_id

    q_result = await db.execute(
        select(QuizQuestion)
        .where(filter_col == filter_val)
        .options(selectinload(QuizQuestion.options))
    )
    questions = {q.id: q for q in q_result.scalars().all()}
    if not questions:
        raise HTTPException(status_code=404, detail="No quiz questions found")

    # Validate all submitted question IDs belong to this quiz
    invalid_qids = [ans.question_id for ans in body.answers if ans.question_id not in questions]
    if invalid_qids:
        raise HTTPException(status_code=400, detail="Invalid question IDs in submission")

    # Score
    correct = 0
    answer_rows = []
    for ans in body.answers:
        q = questions[ans.question_id]
        opt = next((o for o in q.options if o.id == ans.option_id), None)
        if opt is None:
            raise HTTPException(status_code=400, detail=f"Option {ans.option_id} not valid for question {ans.question_id}")
        is_correct = opt.is_correct
        if is_correct:
            correct += 1
        answer_rows.append((ans.question_id, ans.option_id, is_correct))

    total = len(questions)
    score = int(correct / total * 100) if total else 0
    pass_mark = 70
    passed = score >= pass_mark

    attempt = QuizAttempt(
        user_id=user.id,
        module_id=body.module_id,
        tier_id=body.tier_id,
        score=score,
        passed=passed,
        pass_mark=pass_mark,
    )
    db.add(attempt)
    await db.flush()

    for qid, oid, is_correct in answer_rows:
        db.add(QuizAttemptAnswer(
            attempt_id=attempt.id,
            question_id=qid,
            selected_option_id=oid,
            is_correct=is_correct,
        ))

    xp_awarded = 0
    new_badges: list[str] = []
    cert = None

    if passed:
        prev_result = await db.execute(
            select(QuizAttempt).where(
                QuizAttempt.user_id == user.id,
                filter_col == filter_val,
                QuizAttempt.passed == True,
                QuizAttempt.id != attempt.id,
            )
        )
        is_first_pass = prev_result.scalar_one_or_none() is None
        if is_first_pass:
            xp_awarded = await award_xp(db, user, "quiz_first_pass", filter_val)
            await update_streak(db, user)
            new_badges = await check_and_award_badges(db, user, "quiz_passed")

        if body.tier_id:
            cert = await check_and_award_cert(db, user, body.tier_id)

    await db.commit()

    if passed:
        await deliver_webhook(db, user.org_id, "quiz.passed", {
            "user_id": user.id, "module_id": body.module_id, "tier_id": body.tier_id, "score": score,
        })
        for slug in new_badges:
            await deliver_webhook(db, user.org_id, "badge.earned", {
                "user_id": user.id, "badge_slug": slug,
            })
        if cert is not None:
            await deliver_webhook(db, user.org_id, "cert.earned", {
                "user_id": user.id, "cert_id": cert.id,
            })

    explanations = {
        qid: {
            "correct_option_id": next((o.id for o in q.options if o.is_correct), None),
            "explanation": q.explanation,
        }
        for qid, q in questions.items()
    }

    return {
        "score": score,
        "passed": passed,
        "pass_mark": pass_mark,
        "correct": correct,
        "total": total,
        "xp_awarded": xp_awarded,
        "new_badges": new_badges,
        "cert_earned": cert is not None,
        "attempt_id": attempt.id,
        "explanations": explanations,
    }


@router.get("/attempts")
async def my_attempts(
    module_id: int | None = None,
    tier_id: int | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    if limit < 1 or limit > 200:
        limit = 50
    q = select(QuizAttempt).where(QuizAttempt.user_id == user.id)
    if module_id:
        q = q.where(QuizAttempt.module_id == module_id)
    if tier_id:
        q = q.where(QuizAttempt.tier_id == tier_id)
    q = q.order_by(QuizAttempt.started_at.desc()).limit(limit)
    result = await db.execute(q)
    return [
        {
            "id": a.id,
            "module_id": a.module_id,
            "tier_id": a.tier_id,
            "score": a.score,
            "passed": a.passed,
            "started_at": a.started_at,
        }
        for a in result.scalars().all()
    ]

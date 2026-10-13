from sqlalchemy import func, select

from app.models import LearningRole, Module, QuizQuestion, Tier
from app.seed_shipping_from_scratch import ROLE_DATA, seed


def test_every_quiz_question_has_exactly_one_correct_answer():
    for tier in ROLE_DATA["tiers"]:
        for q in tier["quiz"]:
            assert sum(1 for _, correct in q["options"] if correct) == 1, q["q"]


async def test_seed_creates_path_and_is_safe_to_rerun(db_session):
    await seed(db_session)
    await seed(db_session)

    roles = (await db_session.execute(
        select(LearningRole).where(LearningRole.name == "Shipping from Scratch")
    )).scalars().all()
    assert len(roles) == 1
    assert roles[0].audience == "internal"

    tiers = (await db_session.execute(select(Tier).where(Tier.role_id == roles[0].id))).scalars().all()
    assert len(tiers) == 4
    tier_ids = [t.id for t in tiers]
    lessons = await db_session.scalar(select(func.count()).select_from(Module).where(Module.tier_id.in_(tier_ids)))
    assert lessons == 17

    # The last tier's quiz sits on the FuelEU lesson, not the glossary
    glossary = await db_session.scalar(select(Module).where(Module.title.startswith("Shipping Glossary")))
    on_glossary = await db_session.scalar(
        select(func.count()).select_from(QuizQuestion).where(QuizQuestion.module_id == glossary.id)
    )
    assert on_glossary == 0

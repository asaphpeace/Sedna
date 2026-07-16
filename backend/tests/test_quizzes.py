import pytest_asyncio

from app.models.quiz import QuizOption, QuizQuestion
from tests.conftest import auth_headers


@pytest_asyncio.fixture
async def quiz_for_module(db_session, tier_with_modules):
    m1 = tier_with_modules.modules[0]
    q1 = QuizQuestion(module_id=m1.id, question_text="2 + 2?", sort_order=1)
    db_session.add(q1)
    await db_session.flush()
    correct = QuizOption(question_id=q1.id, text="4", is_correct=True, sort_order=1)
    wrong = QuizOption(question_id=q1.id, text="5", is_correct=False, sort_order=2)
    db_session.add_all([correct, wrong])
    await db_session.commit()
    await db_session.refresh(q1)
    await db_session.refresh(correct)
    await db_session.refresh(wrong)
    return m1, q1, correct, wrong


async def test_get_module_quiz_returns_questions(client, user, quiz_for_module):
    m1, q1, correct, wrong = quiz_for_module
    resp = await client.get(f"/quizzes/module/{m1.id}", headers=auth_headers(user))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert {o["id"] for o in body[0]["options"]} == {correct.id, wrong.id}


async def test_submit_correct_answer_passes_and_awards_xp(client, user, quiz_for_module):
    m1, q1, correct, wrong = quiz_for_module
    headers = auth_headers(user)
    resp = await client.post("/quizzes/attempt", headers=headers, json={
        "module_id": m1.id,
        "answers": [{"question_id": q1.id, "option_id": correct.id}],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["passed"] is True
    assert body["score"] == 100
    assert body["xp_awarded"] == 20  # quiz_first_pass XP value


async def test_submit_wrong_answer_fails(client, user, quiz_for_module):
    m1, q1, correct, wrong = quiz_for_module
    resp = await client.post("/quizzes/attempt", headers=auth_headers(user), json={
        "module_id": m1.id,
        "answers": [{"question_id": q1.id, "option_id": wrong.id}],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["passed"] is False
    assert body["score"] == 0


async def test_submit_invalid_option_id_rejected(client, user, quiz_for_module):
    m1, q1, correct, wrong = quiz_for_module
    resp = await client.post("/quizzes/attempt", headers=auth_headers(user), json={
        "module_id": m1.id,
        "answers": [{"question_id": q1.id, "option_id": 999999}],
    })
    assert resp.status_code == 400


async def test_second_pass_does_not_double_award_xp(client, user, quiz_for_module):
    m1, q1, correct, wrong = quiz_for_module
    headers = auth_headers(user)
    body = {"module_id": m1.id, "answers": [{"question_id": q1.id, "option_id": correct.id}]}

    first = await client.post("/quizzes/attempt", headers=headers, json=body)
    assert first.json()["xp_awarded"] == 20

    second = await client.post("/quizzes/attempt", headers=headers, json=body)
    assert second.json()["xp_awarded"] == 0

from tests.conftest import auth_headers


def _question_body(correct_index: int = 0):
    return {
        "question_text": "2 + 2?",
        "explanation": "Basic arithmetic.",
        "sort_order": 0,
        "options": [
            {"text": "4", "is_correct": correct_index == 0},
            {"text": "5", "is_correct": correct_index == 1},
        ],
    }


async def test_non_admin_cannot_manage_quiz(client, user, tier_with_modules):
    m1 = tier_with_modules.modules[0]
    resp = await client.get(f"/admin/modules/{m1.id}/quiz", headers=auth_headers(user))
    assert resp.status_code == 403


async def test_create_question_requires_two_options(client, admin, tier_with_modules):
    m1 = tier_with_modules.modules[0]
    body = _question_body()
    body["options"] = [{"text": "only one", "is_correct": True}]
    resp = await client.post(f"/admin/modules/{m1.id}/quiz/questions", headers=auth_headers(admin), json=body)
    assert resp.status_code == 400


async def test_create_question_requires_exactly_one_correct(client, admin, tier_with_modules):
    m1 = tier_with_modules.modules[0]
    body = _question_body()
    body["options"] = [{"text": "4", "is_correct": True}, {"text": "5", "is_correct": True}]
    resp = await client.post(f"/admin/modules/{m1.id}/quiz/questions", headers=auth_headers(admin), json=body)
    assert resp.status_code == 400


async def test_create_question_exposes_is_correct_to_admin(client, admin, tier_with_modules):
    m1 = tier_with_modules.modules[0]
    resp = await client.post(f"/admin/modules/{m1.id}/quiz/questions", headers=auth_headers(admin), json=_question_body())
    assert resp.status_code == 200
    body = resp.json()
    assert body["question_text"] == "2 + 2?"
    correct = [o for o in body["options"] if o["is_correct"]]
    assert len(correct) == 1
    assert correct[0]["text"] == "4"


async def test_new_question_makes_module_quiz_appear_for_learner(client, admin, user, tier_with_modules):
    m1 = tier_with_modules.modules[0]
    headers_admin = auth_headers(admin)

    before = await client.get(f"/quizzes/module/{m1.id}", headers=auth_headers(user))
    assert before.json() == []

    await client.post(f"/admin/modules/{m1.id}/quiz/questions", headers=headers_admin, json=_question_body())

    after = await client.get(f"/quizzes/module/{m1.id}", headers=auth_headers(user))
    assert len(after.json()) == 1
    # Learner-facing endpoint must NOT expose is_correct
    assert "is_correct" not in after.json()[0]["options"][0]


async def test_update_question_replaces_options(client, admin, tier_with_modules):
    m1 = tier_with_modules.modules[0]
    headers = auth_headers(admin)
    created = await client.post(f"/admin/modules/{m1.id}/quiz/questions", headers=headers, json=_question_body())
    qid = created.json()["id"]

    updated_body = _question_body(correct_index=1)
    updated_body["question_text"] = "2 + 3?"
    resp = await client.patch(f"/admin/quiz-questions/{qid}", headers=headers, json=updated_body)
    assert resp.status_code == 200
    body = resp.json()
    assert body["question_text"] == "2 + 3?"
    correct = [o for o in body["options"] if o["is_correct"]]
    assert correct[0]["text"] == "5"


async def test_delete_question(client, admin, tier_with_modules):
    m1 = tier_with_modules.modules[0]
    headers = auth_headers(admin)
    created = await client.post(f"/admin/modules/{m1.id}/quiz/questions", headers=headers, json=_question_body())
    qid = created.json()["id"]

    resp = await client.delete(f"/admin/quiz-questions/{qid}", headers=headers)
    assert resp.status_code == 200

    listed = await client.get(f"/admin/modules/{m1.id}/quiz", headers=headers)
    assert listed.json() == []


async def test_full_quiz_flow_scores_and_shows_results(client, admin, user, tier_with_modules):
    """End-to-end: author a question as admin, take it as a learner, confirm scoring."""
    m1 = tier_with_modules.modules[0]
    created = await client.post(
        f"/admin/modules/{m1.id}/quiz/questions", headers=auth_headers(admin), json=_question_body()
    )
    question = created.json()
    correct_option = next(o for o in question["options"] if o["is_correct"])

    resp = await client.post("/quizzes/attempt", headers=auth_headers(user), json={
        "module_id": m1.id,
        "answers": [{"question_id": question["id"], "option_id": correct_option["id"]}],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["passed"] is True
    assert body["score"] == 100
    assert body["correct"] == 1

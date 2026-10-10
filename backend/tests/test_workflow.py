"""End-to-end integration tests for the test-taking workflow.

Covers the full happy path (exam -> subject -> question -> test -> publish ->
assign -> start -> answer -> submit -> result -> report) plus the key safety
guarantees: answer-key hiding, duplicate-submission protection, ownership
checks and report endpoints.
"""

API = "/api/v1"


def _create_exam(client, headers, unique):
    response = client.post(
        f"{API}/exams/",
        json={
            "name": f"Workflow Exam {unique}",
            "code": f"EX{unique}",
            "exam_type": "CUSTOM",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_subject(client, headers, exam_id, unique):
    response = client.post(
        f"{API}/subjects/",
        json={"exam_id": exam_id, "name": f"Subject {unique}", "code": f"SUB{unique}"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_question(client, headers, subject_id):
    response = client.post(
        f"{API}/questions/",
        json={
            "subject_id": subject_id,
            "question_type": "SINGLE_CHOICE",
            "question_text": "What is 2 + 2?",
            "explanation": "Basic arithmetic.",
            "difficulty": "EASY",
            "marks": 4.0,
            "negative_marks": 1.0,
            "status": "PUBLISHED",
            "options": [
                {"option_text": "3", "option_order": 1, "is_correct": False},
                {"option_text": "4", "option_order": 2, "is_correct": True},
            ],
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    correct = next(option for option in body["options"] if option["is_correct"])
    return body["id"], correct["id"]


def _create_published_test(client, headers, exam_id, question_id, unique):
    response = client.post(
        f"{API}/tests/",
        json={
            "exam_id": exam_id,
            "name": f"Workflow Test {unique}",
            "code": f"T{unique}",
            "duration_minutes": 60,
            "max_attempts": 2,
            "negative_marking_enabled": True,
            "negative_marks": 1.0,
            "passing_marks": 3.0,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    test_id = response.json()["id"]

    add = client.post(
        f"{API}/tests/{test_id}/questions",
        json={"question_id": question_id},
        headers=headers,
    )
    assert add.status_code == 201, add.text
    assert add.json()["question_id"] == question_id
    assert add.json()["question_order"] == 1

    publish = client.post(f"{API}/tests/{test_id}/publish", headers=headers)
    assert publish.status_code == 200, publish.text
    assert publish.json()["status"] == "PUBLISHED"
    assert float(publish.json()["total_marks"]) == 4.0
    return test_id


def test_full_student_workflow(client, admin_headers, student_headers, unique):
    exam_id = _create_exam(client, admin_headers, unique)
    subject_id = _create_subject(client, admin_headers, exam_id, unique)
    question_id, correct_option_id = _create_question(client, admin_headers, subject_id)
    test_id = _create_published_test(
        client, admin_headers, exam_id, question_id, unique
    )

    me = client.get(f"{API}/auth/me", headers=student_headers)
    student_id = me.json()["id"]

    # Assign the test to the student.
    assignment = client.post(
        f"{API}/assignments/",
        json={"test_id": test_id, "student_id": student_id},
        headers=admin_headers,
    )
    assert assignment.status_code == 201, assignment.text

    # The student sees the test as startable.
    listing = client.get(f"{API}/student/tests", headers=student_headers)
    assert listing.status_code == 200, listing.text
    row = next(item for item in listing.json() if item["test"]["id"] == test_id)
    assert row["can_attempt"] is True

    # Start the attempt.
    start = client.post(
        f"{API}/student/tests/{test_id}/start", headers=student_headers
    )
    assert start.status_code == 201, start.text
    start_body = start.json()
    attempt_id = start_body["attempt"]["id"]
    assert start_body["attempt"]["status"] == "STARTED"

    # Answer keys must never leak to the student.
    first_question = start_body["questions"][0]
    assert "explanation" not in first_question
    assert "is_correct" not in first_question["options"][0]

    # Save a correct answer.
    save = client.put(
        f"{API}/student/attempts/{attempt_id}/answers",
        json={
            "answers": [
                {"question_id": question_id, "selected_option_id": correct_option_id}
            ]
        },
        headers=student_headers,
    )
    assert save.status_code == 200, save.text
    assert save.json()["answered_count"] == 1

    # Submit and score.
    submit = client.post(
        f"{API}/student/attempts/{attempt_id}/submit", headers=student_headers
    )
    assert submit.status_code == 200, submit.text
    submit_body = submit.json()
    assert submit_body["score"] == 4.0
    assert submit_body["max_score"] == 4.0
    assert submit_body["percentage"] == 100.0
    assert submit_body["pass_status"] is True
    result_id = submit_body["result_id"]

    # A second submission must not create a second result.
    duplicate = client.post(
        f"{API}/student/attempts/{attempt_id}/submit", headers=student_headers
    )
    assert duplicate.status_code == 409, duplicate.text
    assert duplicate.json()["error"]["code"] == "ATTEMPT_ALREADY_SUBMITTED"

    # Saving answers after submit is refused too.
    late_save = client.put(
        f"{API}/student/attempts/{attempt_id}/answers",
        json={"answers": [{"question_id": question_id, "selected_option_id": correct_option_id}]},
        headers=student_headers,
    )
    assert late_save.status_code == 409

    # Review exposes the answer key only after evaluation.
    review = client.get(
        f"{API}/student/results/{result_id}/review", headers=student_headers
    )
    assert review.status_code == 200, review.text
    reviewed = review.json()["answers"][0]
    assert reviewed["is_correct"] is True
    assert reviewed["marks_awarded"] == 4.0
    assert reviewed["explanation"] == "Basic arithmetic."

    # Student result listing includes the attempt.
    my_results = client.get(f"{API}/student/results", headers=student_headers)
    assert my_results.status_code == 200
    assert any(item["id"] == result_id for item in my_results.json())

    # Admin views and publishes the result.
    detail = client.get(f"{API}/attempts/{attempt_id}", headers=admin_headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["attempt"]["status"] == "EVALUATED"

    answers = client.get(f"{API}/attempts/{attempt_id}/answers", headers=admin_headers)
    assert answers.status_code == 200
    assert answers.json()[0]["is_correct"] is True

    publish = client.post(f"{API}/results/{result_id}/publish", headers=admin_headers)
    assert publish.status_code == 200, publish.text
    assert publish.json()["published_at"] is not None

    republish = client.post(f"{API}/results/{result_id}/publish", headers=admin_headers)
    assert republish.status_code == 409

    # Reports all render.
    for path in (
        "/reports/dashboard",
        "/reports/exams",
        "/reports/tests",
        "/reports/questions",
        "/reports/subjects",
    ):
        response = client.get(f"{API}{path}", headers=admin_headers)
        assert response.status_code == 200, (path, response.text)

    student_report = client.get(
        f"{API}/reports/students/{student_id}", headers=admin_headers
    )
    assert student_report.status_code == 200, student_report.text
    assert student_report.json()["student_id"] == student_id

    export = client.get(f"{API}/results/export", headers=admin_headers)
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    assert "result_id" in export.text


def test_student_cannot_read_another_students_attempt(
    client, admin_headers, student_headers, unique
):
    """Ownership check: a fresh student gets 404 for someone else's attempt."""
    # Create a second student and give them an attempt via the seeded flow.
    from app.core.security import hash_password
    from app.models.user import User
    from app.utils.enums import UserStatus

    # Use the admin API to create a distinct student account.
    suffix = unique.lower()
    created = client.post(
        f"{API}/users/",
        json={
            "username": f"intruder_{suffix}",
            "email": f"intruder_{suffix}@example.com",
            "password": "Admin@123",
            "first_name": "In",
            "last_name": "Truder",
            "status": UserStatus.ACTIVE.value,
        },
        headers=admin_headers,
    )
    assert created.status_code == 201, created.text

    # Find the seeded student's most recent attempt id via the admin listing.
    attempts = client.get(
        f"{API}/attempts/", params={"page_size": 1}, headers=admin_headers
    )
    assert attempts.status_code == 200
    items = attempts.json()["items"]
    if not items:
        return  # nothing to check in this environment

    attempt_id = items[0]["attempt_id"] if "attempt_id" in items[0] else items[0]["id"]

    # Log in as the newly created (non-owner) user.
    login = client.post(
        f"{API}/auth/login",
        json={"username": f"intruder_{suffix}", "password": "Admin@123"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.get(f"{API}/student/attempts/{attempt_id}", headers=headers)
    assert response.status_code == 404, response.text

"""Integration tests for the XLSX test-import endpoints.

The workbooks are produced with the app's own dependency-free writer, so the
tests exercise the reader/parser and the whole upload -> validate -> persist
flow without needing a third-party spreadsheet library.
"""

from app.utils.xlsx import read_xlsx, write_xlsx

API = "/api/v1"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _create_exam(client, headers, unique):
    response = client.post(
        f"{API}/exams/",
        json={"name": f"Import Exam {unique}", "code": f"IMP{unique}", "exam_type": "CUSTOM"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _workbook(
    *,
    name: str,
    code: str,
    subject_code: str,
    question_text: str = "What is 2 + 2?",
    question_type: str = "SINGLE_CHOICE",
    options=("3", "4", "5", "6"),
    correct: str = "2",
    topic: str = "Arithmetic",
) -> bytes:
    test_sheet = [
        ["Field", "Value"],
        ["name", name],
        ["code", code],
        ["duration_minutes", 60],
        ["passing_marks", 2],
        ["negative_marking_enabled", "TRUE"],
        ["negative_marks", 1],
    ]
    option_count = 4
    question_sheet = [
        [
            "subject_code",
            "subject_name",
            "topic",
            "question_text",
            "question_type",
            "difficulty",
            "marks",
            "negative_marks",
            *[f"option_{index}" for index in range(1, option_count + 1)],
            "correct_options",
        ],
        [
            subject_code,
            f"Subject {subject_code}",
            topic,
            question_text,
            question_type,
            "EASY",
            4,
            1,
            *list(options),
            *([""] * (option_count - len(options))),
            correct,
        ],
    ]
    return write_xlsx([("Test", test_sheet), ("Questions", question_sheet)])


def _import(client, headers, exam_id, data: bytes, filename: str = "import.xlsx"):
    return client.post(
        f"{API}/tests/import",
        data={"exam_id": str(exam_id)},
        files={"file": (filename, data, XLSX_MIME)},
        headers=headers,
    )


def test_import_happy_path_creates_test_questions_subject_and_topic(
    client, admin_headers, unique
):
    exam_id = _create_exam(client, admin_headers, unique)
    subject_code = f"PHY{unique}"
    data = _workbook(
        name=f"Imported Test {unique}",
        code=f"IT{unique}",
        subject_code=subject_code,
    )

    response = _import(client, admin_headers, exam_id, data)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "DRAFT"
    assert body["test_code"] == f"IT{unique}"
    assert body["questions_created"] == 1
    assert body["subjects_created"] == 1
    assert body["topics_created"] == 1
    assert body["total_marks"] == 4.0

    test_id = body["test_id"]
    attached = client.get(f"{API}/tests/{test_id}/questions", headers=admin_headers)
    assert attached.status_code == 200, attached.text
    links = attached.json()
    assert len(links) == 1

    question = client.get(
        f"{API}/questions/{links[0]['question_id']}", headers=admin_headers
    )
    assert question.status_code == 200, question.text
    assert question.json()["status"] == "DRAFT"

    # The subject was created inside the chosen exam under the requested code.
    subjects = client.get(
        f"{API}/subjects/", params={"exam_id": exam_id, "page_size": 100}, headers=admin_headers
    )
    assert subjects.status_code == 200, subjects.text
    codes = {item["code"] for item in subjects.json()["items"]}
    assert subject_code in codes


def test_second_import_reuses_existing_subject_and_topic(
    client, admin_headers, unique
):
    exam_id = _create_exam(client, admin_headers, unique)
    subject_code = f"CHM{unique}"
    first = _import(
        client,
        admin_headers,
        exam_id,
        _workbook(name=f"First {unique}", code=f"F{unique}", subject_code=subject_code),
    )
    assert first.status_code == 201, first.text
    assert first.json()["subjects_created"] == 1

    second = _import(
        client,
        admin_headers,
        exam_id,
        _workbook(name=f"Second {unique}", code=f"S{unique}", subject_code=subject_code),
    )
    assert second.status_code == 201, second.text
    assert second.json()["subjects_created"] == 0
    assert second.json()["topics_created"] == 0


def test_import_duplicate_code_conflict(client, admin_headers, unique):
    exam_id = _create_exam(client, admin_headers, unique)
    code = f"DUP{unique}"
    data = _workbook(name=f"Dup A {unique}", code=code, subject_code=f"Z{unique}")
    assert _import(client, admin_headers, exam_id, data).status_code == 201

    repeat = _import(
        client, admin_headers, exam_id, _workbook(name="Dup B", code=code, subject_code=f"Z{unique}")
    )
    assert repeat.status_code == 409
    assert repeat.json()["error"]["code"] == "TEST_CODE_EXISTS"


def test_import_validation_errors_are_reported_per_row(client, admin_headers, unique):
    exam_id = _create_exam(client, admin_headers, unique)
    data = _workbook(
        name=f"Bad {unique}",
        code=f"B{unique}",
        subject_code=f"B{unique}",
        question_text="",  # missing stem
        question_type="NOPE",  # unknown type
        options=("a", "b"),
        correct="9",  # no matching option
    )
    response = _import(client, admin_headers, exam_id, data)
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "TEST_IMPORT_INVALID"
    errors = payload["error"]["details"]["errors"]
    fields = {error["field"] for error in errors}
    assert "question_text" in fields
    assert "question_type" in fields
    assert "correct_options" in fields


def test_import_unknown_exam(client, admin_headers, unique):
    data = _workbook(name=f"No Exam {unique}", code=f"N{unique}", subject_code=f"N{unique}")
    response = _import(client, admin_headers, 999_999_999, data)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EXAM_NOT_FOUND"


def test_import_without_questions_is_rejected(client, admin_headers, unique):
    exam_id = _create_exam(client, admin_headers, unique)
    blank = write_xlsx(
        [
            ("Test", [["Field", "Value"], ["name", "Empty"], ["code", f"E{unique}"]]),
            ("Questions", [["subject_code", "question_text"]]),
        ]
    )
    response = _import(client, admin_headers, exam_id, blank)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "TEST_IMPORT_INVALID"


def test_import_rejects_non_xlsx_payload(client, admin_headers, unique):
    exam_id = _create_exam(client, admin_headers, unique)
    response = _import(client, admin_headers, exam_id, b"not a spreadsheet")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "TEST_IMPORT_INVALID"


def test_import_requires_permissions(client, student_headers, unique, admin_headers):
    exam_id = _create_exam(client, admin_headers, unique)
    data = _workbook(name=f"Perm {unique}", code=f"P{unique}", subject_code=f"P{unique}")
    response = _import(client, student_headers, exam_id, data)
    assert response.status_code == 403


def test_template_download_is_a_valid_workbook(client, admin_headers):
    response = client.get(f"{API}/tests/import/template", headers=admin_headers)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    workbook = read_xlsx(response.content)
    assert {"Test", "Questions"} <= set(workbook)

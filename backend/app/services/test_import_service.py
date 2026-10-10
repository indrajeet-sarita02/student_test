"""XLSX test-import service.

Turns an uploaded workbook into a brand-new ``DRAFT`` test and its questions in a
single transaction:

* the ``Test`` sheet (``Field`` / ``Value`` rows) provides the test settings;
* the ``Questions`` sheet provides one question per row.

Subjects/topics referenced by ``code``/``name`` are created on demand inside the
selected exam (see :func:`_resolve_subject` / :func:`_resolve_topic`), imported
questions are always ``DRAFT`` and the test's ``total_marks`` is recomputed from
the attached questions.

Validation is **all-or-nothing**: the workbook is fully parsed and checked
*before* anything is written, and any problem is reported as a
``TEST_IMPORT_INVALID`` (422) error whose ``details.errors`` lists every bad row.
"""

import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import Request
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationAppError,
)
from app.models.subject import Subject
from app.models.test import Test, TestQuestion
from app.models.topic import Topic
from app.repositories import exam_repository
from app.repositories import test_repository
from app.schemas.question import OptionCreate, QuestionImportItem
from app.schemas.test import TestCreate, TestImportResponse
from app.services import question_service
from app.services.audit_service import record_audit
from app.utils.enums import Difficulty, QuestionStatus, QuestionType, TestStatus
from app.utils.xlsx import read_xlsx, write_xlsx

#: Workbook sheets consumed by the importer (matched case-insensitively).
TEST_SHEET = "Test"
QUESTIONS_SHEET = "Questions"
INSTRUCTIONS_SHEET = "Instructions"

#: Hard limits protecting the request from oversized payloads.
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_QUESTIONS = 500

#: Canonical ``Questions`` sheet columns, used by the template generator too.
QUESTION_COLUMNS: Tuple[str, ...] = (
    "subject_code",
    "subject_name",
    "topic",
    "question_text",
    "question_type",
    "difficulty",
    "marks",
    "negative_marks",
    "explanation",
    "source",
    "option_1",
    "option_2",
    "option_3",
    "option_4",
    "option_5",
    "option_6",
    "correct_options",
)

#: Header aliases -> canonical column name (headers are normalised first).
_HEADER_ALIASES: Dict[str, str] = {
    "subject_code": "subject_code",
    "subject": "subject_code",
    "subject_name": "subject_name",
    "topic": "topic",
    "topic_name": "topic",
    "question_text": "question_text",
    "question": "question_text",
    "text": "question_text",
    "question_type": "question_type",
    "type": "question_type",
    "difficulty": "difficulty",
    "level": "difficulty",
    "marks": "marks",
    "mark": "marks",
    "score": "marks",
    "negative_marks": "negative_marks",
    "negative": "negative_marks",
    "explanation": "explanation",
    "solution": "explanation",
    "source": "source",
    "reference": "source",
    "correct_options": "correct_options",
    "correct": "correct_options",
    "answer": "correct_options",
    "answers": "correct_options",
    "correct_answer": "correct_options",
    "answer_key": "correct_options",
}

_OPTION_HEADER = re.compile(r"^option_?([1-9a-f])$")

_QUESTION_TYPES: Dict[str, str] = {
    "single_choice": QuestionType.SINGLE_CHOICE.value,
    "single": QuestionType.SINGLE_CHOICE.value,
    "singlechoice": QuestionType.SINGLE_CHOICE.value,
    "mcq": QuestionType.SINGLE_CHOICE.value,
    "multiple_choice": QuestionType.MULTIPLE_CHOICE.value,
    "multiple": QuestionType.MULTIPLE_CHOICE.value,
    "multichoice": QuestionType.MULTIPLE_CHOICE.value,
    "multi": QuestionType.MULTIPLE_CHOICE.value,
    "msq": QuestionType.MULTIPLE_CHOICE.value,
    "true_false": QuestionType.TRUE_FALSE.value,
    "truefalse": QuestionType.TRUE_FALSE.value,
    "tf": QuestionType.TRUE_FALSE.value,
    "boolean": QuestionType.TRUE_FALSE.value,
    "numerical": QuestionType.NUMERICAL.value,
    "numeric": QuestionType.NUMERICAL.value,
    "num": QuestionType.NUMERICAL.value,
    "subjective": QuestionType.SUBJECTIVE.value,
    "descriptive": QuestionType.SUBJECTIVE.value,
    "essay": QuestionType.SUBJECTIVE.value,
}

_DIFFICULTIES: Dict[str, str] = {
    "easy": Difficulty.EASY.value,
    "medium": Difficulty.MEDIUM.value,
    "hard": Difficulty.HARD.value,
}

_TRUE_VALUES = {"true", "t", "yes", "y", "1"}
_FALSE_VALUES = {"false", "f", "no", "n", "0"}


@dataclass
class _QuestionRow:
    """A validated ``Questions`` sheet row, ready to persist."""

    row: int
    subject_code: str
    subject_name: Optional[str]
    topic_name: Optional[str]
    question_type: str
    question_text: str
    explanation: Optional[str]
    difficulty: str
    marks: float
    negative_marks: float
    source: Optional[str]
    options: List[OptionCreate]


# --------------------------------------------------------------------------- #
# Small coercion helpers
# --------------------------------------------------------------------------- #
def _text(value: Any) -> str:
    return ("" if value is None else str(value)).strip()


def _normalise_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _text(value).lower()).strip("_")


def _bool_value(raw: str, default: bool) -> bool:
    low = raw.strip().lower()
    if not low:
        return default
    if low in _TRUE_VALUES:
        return True
    if low in _FALSE_VALUES:
        return False
    raise ValueError(f"expected a boolean (TRUE/FALSE), got {raw!r}")


def _int_value(raw: str, default: int) -> int:
    if not raw.strip():
        return default
    return int(float(raw))


def _float_value(raw: str, default: float) -> float:
    if not raw.strip():
        return default
    return float(raw)


def _datetime_value(raw: str) -> Optional[datetime]:
    value = raw.strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    for pattern in (
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y",
        "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            continue
    raise ValueError(f"expected a date/time such as 2026-04-01 10:00, got {raw!r}")


def _option_texts(row: Sequence[str], option_columns: Dict[int, int]) -> Dict[int, str]:
    texts: Dict[int, str] = {}
    for order, column in option_columns.items():
        value = _text(row[column]) if column < len(row) else ""
        if value:
            texts[order] = value
    return texts


def _parse_correct_options(raw: str, texts: Dict[int, str]) -> Tuple[set, Optional[str]]:
    """Parse the ``correct_options`` cell into a set of 1-based option numbers."""
    if not raw.strip():
        return set(), None
    chosen: set = set()
    for token in re.split(r"[,;/|\s]+", raw.strip()):
        if not token:
            continue
        low = token.lower()
        if low in ("true", "t"):
            match = next((o for o, t in texts.items() if t.strip().lower() == "true"), None)
            if match is None:
                return set(), "'TRUE' does not match any option text"
            chosen.add(match)
            continue
        if low in ("false", "f"):
            match = next((o for o, t in texts.items() if t.strip().lower() == "false"), None)
            if match is None:
                return set(), "'FALSE' does not match any option text"
            chosen.add(match)
            continue
        if token.isdigit():
            order = int(token)
        elif len(token) == 1 and token.isalpha():
            order = ord(token.upper()) - ord("A") + 1
        else:
            return set(), f"unrecognised correct option {token!r}"
        if order not in texts:
            return set(), f"correct option {token!r} has no matching option column"
        chosen.add(order)
    return chosen, None


# --------------------------------------------------------------------------- #
# Sheet parsing
# --------------------------------------------------------------------------- #
def _sheet(workbook: Dict[str, List[List[str]]], name: str) -> Optional[List[List[str]]]:
    target = name.lower()
    for sheet_name, rows in workbook.items():
        if sheet_name.strip().lower() == target:
            return rows
    return None


def _parse_test_sheet(rows: Sequence[Sequence[str]], errors: List[Dict[str, Any]]) -> Dict[str, str]:
    """Turn the ``Field`` / ``Value`` sheet into a ``{field: raw_value}`` map."""
    values: Dict[str, str] = {}
    for index, row in enumerate(rows, start=1):
        key = _normalise_header(row[0]) if row else ""
        if not key or key == "field":
            continue
        value = _text(row[1]) if len(row) > 1 else ""
        values[key] = value
    return values


def _build_test_kwargs(
    exam_id: int, raw: Dict[str, str], errors: List[Dict[str, Any]]
) -> Optional[TestCreate]:
    start_errors = len(errors)
    name = _text(raw.get("name"))
    code = _text(raw.get("code"))
    if not name:
        errors.append({"row": None, "field": "name", "message": "Test name is required."})
    if not code:
        errors.append({"row": None, "field": "code", "message": "Test code is required."})

    def safe(field: str, parser, default):
        value = raw.get(field)
        if value is None:
            return default
        try:
            return parser(value)
        except (TypeError, ValueError) as exc:
            errors.append({"row": None, "field": field, "message": str(exc)})
            return default

    kwargs: Dict[str, Any] = {
        "exam_id": exam_id,
        "name": name,
        "code": code,
        "description": raw.get("description") or None,
        "instructions": raw.get("instructions") or None,
        "duration_minutes": safe("duration_minutes", lambda v: _int_value(v, 180), 180),
        "total_marks": safe("total_marks", lambda v: _float_value(v, 0.0), 0.0),
        "passing_marks": (
            None if "passing_marks" not in raw or not _text(raw.get("passing_marks"))
            else safe("passing_marks", lambda v: _float_value(v, 0.0), None)
        ),
        "negative_marking_enabled": safe(
            "negative_marking_enabled", lambda v: _bool_value(v, True), True
        ),
        "negative_marks": safe("negative_marks", lambda v: _float_value(v, 1.0), 1.0),
        "randomize_questions": safe(
            "randomize_questions", lambda v: _bool_value(v, False), False
        ),
        "randomize_options": safe(
            "randomize_options", lambda v: _bool_value(v, False), False
        ),
        "max_attempts": safe("max_attempts", lambda v: _int_value(v, 1), 1),
        "scheduled_start_at": safe("scheduled_start_at", _datetime_value, None),
        "scheduled_end_at": safe("scheduled_end_at", _datetime_value, None),
    }

    if len(errors) > start_errors:  # avoid a second wave of confusing pydantic errors
        return None
    try:
        return TestCreate(**kwargs)
    except ValidationError as exc:
        for error in exc.errors():
            field = ".".join(str(part) for part in error.get("loc", ()))
            errors.append(
                {"row": None, "field": field or "Test", "message": error.get("msg", "Invalid value")}
            )
        return None


def _parse_questions_sheet(
    rows: Sequence[Sequence[str]], errors: List[Dict[str, Any]]
) -> List[_QuestionRow]:
    start_errors = len(errors)
    if not rows:
        errors.append(
            {"row": None, "field": QUESTIONS_SHEET, "message": "The Questions sheet is empty."}
        )
        return []

    # Locate the header row and map every recognised column.
    header_index = -1
    columns: Dict[str, int] = {}
    option_columns: Dict[int, int] = {}
    for index, row in enumerate(rows):
        mapping: Dict[str, int] = {}
        options: Dict[int, int] = {}
        for col, cell in enumerate(row):
            normalised = _normalise_header(cell)
            if not normalised:
                continue
            option_match = _OPTION_HEADER.match(normalised)
            if option_match:
                token = option_match.group(1)
                order = int(token) if token.isdigit() else ord(token) - ord("a") + 1
                options[order] = col
            elif normalised in _HEADER_ALIASES:
                mapping[_HEADER_ALIASES[normalised]] = col
        if "question_text" in mapping or "subject_code" in mapping:
            header_index = index
            columns = mapping
            option_columns = options
            break

    if header_index < 0:
        errors.append(
            {
                "row": None,
                "field": QUESTIONS_SHEET,
                "message": (
                    "Could not find the header row. The first row must contain at least "
                    "the 'subject_code' and 'question_text' columns."
                ),
            }
        )
        return []

    if "subject_code" not in columns:
        errors.append(
            {"row": None, "field": "subject_code", "message": "The 'subject_code' column is required."}
        )
    if "question_text" not in columns:
        errors.append(
            {"row": None, "field": "question_text", "message": "The 'question_text' column is required."}
        )
    if len(errors) > start_errors:
        return []

    parsed: List[_QuestionRow] = []

    def pick(row: Sequence[str], column: Optional[int]) -> str:
        if column is None or column >= len(row):
            return ""
        return _text(row[column])

    for offset, row in enumerate(rows[header_index + 1 :], start=1):
        if not any(_text(cell) for cell in row):
            continue  # blank separator row
        row_number = header_index + 1 + offset
        if len(parsed) >= MAX_QUESTIONS:
            errors.append(
                {
                    "row": row_number,
                    "field": None,
                    "message": f"Too many rows - a single import supports at most {MAX_QUESTIONS} questions.",
                }
            )
            break

        subject_code = pick(row, columns.get("subject_code"))
        question_text = pick(row, columns.get("question_text"))
        if not subject_code:
            errors.append({"row": row_number, "field": "subject_code", "message": "Required."})
        if not question_text:
            errors.append({"row": row_number, "field": "question_text", "message": "Required."})

        raw_type = pick(row, columns.get("question_type")) or QuestionType.SINGLE_CHOICE.value
        question_type = _QUESTION_TYPES.get(_normalise_header(raw_type))
        if question_type is None:
            errors.append(
                {
                    "row": row_number,
                    "field": "question_type",
                    "message": f"Unknown question type {raw_type!r}.",
                }
            )

        raw_difficulty = pick(row, columns.get("difficulty")) or Difficulty.MEDIUM.value
        difficulty = _DIFFICULTIES.get(_normalise_header(raw_difficulty))
        if difficulty is None:
            errors.append(
                {
                    "row": row_number,
                    "field": "difficulty",
                    "message": f"Unknown difficulty {raw_difficulty!r}.",
                }
            )

        try:
            marks = _float_value(pick(row, columns.get("marks")), 4.0)
        except ValueError:
            errors.append({"row": row_number, "field": "marks", "message": "Must be a number."})
            marks = 4.0
        try:
            negative_marks = _float_value(pick(row, columns.get("negative_marks")), 0.0)
        except ValueError:
            errors.append(
                {"row": row_number, "field": "negative_marks", "message": "Must be a number."}
            )
            negative_marks = 0.0
        if marks < 0:
            errors.append({"row": row_number, "field": "marks", "message": "Must be zero or more."})
        if negative_marks < 0:
            errors.append(
                {"row": row_number, "field": "negative_marks", "message": "Must be zero or more."}
            )

        option_texts = _option_texts(row, option_columns)
        correct, correct_error = _parse_correct_options(
            pick(row, columns.get("correct_options")), option_texts
        )
        if correct_error:
            errors.append(
                {"row": row_number, "field": "correct_options", "message": correct_error}
            )

        options = [
            OptionCreate(option_text=text, option_order=order, is_correct=order in correct)
            for order, text in sorted(option_texts.items())
        ]
        if question_type is not None and not correct_error:
            try:
                question_service._validate_options(question_type, options)  # noqa: SLF001
            except Exception as exc:  # AppError carries the human message
                errors.append(
                    {
                        "row": row_number,
                        "field": "options",
                        "message": getattr(exc, "message", str(exc)),
                    }
                )

        parsed.append(
            _QuestionRow(
                row=row_number,
                subject_code=subject_code,
                subject_name=pick(row, columns.get("subject_name")) or None,
                topic_name=pick(row, columns.get("topic")) or None,
                question_type=question_type or QuestionType.SINGLE_CHOICE.value,
                question_text=question_text,
                explanation=pick(row, columns.get("explanation")) or None,
                difficulty=difficulty or Difficulty.MEDIUM.value,
                marks=marks,
                negative_marks=negative_marks,
                source=pick(row, columns.get("source")) or None,
                options=options,
            )
        )
    return parsed


# --------------------------------------------------------------------------- #
# Persistence helpers
# --------------------------------------------------------------------------- #
def _resolve_subject(
    db: Session,
    exam_id: int,
    code: str,
    name: Optional[str],
    cache: Dict[str, Subject],
    counters: Dict[str, int],
) -> Subject:
    key = code.strip().lower()
    if key in cache:
        return cache[key]

    subject = db.scalar(
        select(Subject)
        .where(Subject.exam_id == exam_id, func.lower(Subject.code) == key)
        .limit(1)
    )
    if subject is None:
        subject = Subject(
            exam_id=exam_id,
            name=(name or code).strip(),
            code=code.strip(),
            sort_order=0,
            is_active=True,
        )
        try:
            with db.begin_nested():
                db.add(subject)
                db.flush()
        except IntegrityError:  # concurrent insert won the race
            subject = db.scalar(
                select(Subject)
                .where(Subject.exam_id == exam_id, func.lower(Subject.code) == key)
                .limit(1)
            )
            if subject is None:  # pragma: no cover - defensive
                raise
        else:
            counters["subjects"] += 1

    cache[key] = subject
    return subject


def _resolve_topic(
    db: Session,
    subject: Subject,
    name: Optional[str],
    cache: Dict[int, Dict[str, Topic]],
    counters: Dict[str, int],
) -> Optional[Topic]:
    if not name or not name.strip():
        return None
    key = name.strip().lower()
    subject_topics = cache.setdefault(subject.id, {})
    if key in subject_topics:
        return subject_topics[key]

    topic = db.scalar(
        select(Topic)
        .where(Topic.subject_id == subject.id, func.lower(Topic.name) == key)
        .limit(1)
    )
    if topic is None:
        topic = Topic(subject_id=subject.id, name=name.strip(), sort_order=0, is_active=True)
        db.add(topic)
        db.flush()
        counters["topics"] += 1
    subject_topics[key] = topic
    return topic


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def import_test_from_xlsx(
    db: Session,
    *,
    data: bytes,
    exam_id: int,
    user_id: int,
    filename: Optional[str] = None,
    request: Optional[Request] = None,
) -> TestImportResponse:
    """Create a ``DRAFT`` test and its questions from an XLSX upload."""
    if not data:
        raise ValidationAppError(
            "The uploaded file is empty.", code="TEST_IMPORT_INVALID"
        )
    if len(data) > MAX_FILE_BYTES:
        raise ValidationAppError(
            f"The file is larger than the {MAX_FILE_BYTES // (1024 * 1024)} MB limit.",
            code="TEST_IMPORT_INVALID",
        )
    if exam_repository.get_exam(db, exam_id) is None:
        raise NotFoundError("Exam was not found.", code="EXAM_NOT_FOUND")

    try:
        workbook = read_xlsx(data)
    except (zipfile.BadZipFile, KeyError, ValueError) as exc:
        raise ValidationAppError(
            "The file is not a valid .xlsx workbook.", code="TEST_IMPORT_INVALID"
        ) from exc

    errors: List[Dict[str, Any]] = []
    test_rows = _sheet(workbook, TEST_SHEET)
    question_rows = _sheet(workbook, QUESTIONS_SHEET)
    if test_rows is None:
        errors.append(
            {
                "row": None,
                "field": TEST_SHEET,
                "message": f"A '{TEST_SHEET}' sheet is required.",
            }
        )
    if question_rows is None:
        errors.append(
            {
                "row": None,
                "field": QUESTIONS_SHEET,
                "message": f"A '{QUESTIONS_SHEET}' sheet is required.",
            }
        )
    if errors:
        raise ValidationAppError(
            "The import file is not structured correctly.",
            code="TEST_IMPORT_INVALID",
            details={"errors": errors},
        )

    raw_test = _parse_test_sheet(test_rows or [], errors)
    payload = _build_test_kwargs(exam_id, raw_test, errors)
    question_data = _parse_questions_sheet(question_rows or [], errors)
    if not question_data and not errors:
        errors.append(
            {"row": None, "field": QUESTIONS_SHEET, "message": "At least one question is required."}
        )

    if errors:
        raise ValidationAppError(
            f"The import file has {len(errors)} problem(s).",
            code="TEST_IMPORT_INVALID",
            details={"errors": errors},
        )
    assert payload is not None  # guaranteed by the error check above

    if test_repository.test_code_exists(db, payload.code):
        raise ConflictError(
            "A test with this code already exists.", code="TEST_CODE_EXISTS"
        )

    counters = {"subjects": 0, "topics": 0}
    subject_cache: Dict[str, Subject] = {}
    topic_cache: Dict[int, Dict[str, Topic]] = {}

    test = Test(
        exam_id=exam_id,
        name=payload.name,
        code=payload.code,
        description=payload.description,
        instructions=payload.instructions,
        duration_minutes=payload.duration_minutes,
        total_marks=payload.total_marks,
        passing_marks=payload.passing_marks,
        negative_marking_enabled=payload.negative_marking_enabled,
        negative_marks=payload.negative_marks,
        randomize_questions=payload.randomize_questions,
        randomize_options=payload.randomize_options,
        max_attempts=payload.max_attempts,
        status=TestStatus.DRAFT.value,
        scheduled_start_at=payload.scheduled_start_at,
        scheduled_end_at=payload.scheduled_end_at,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(test)

    try:
        db.flush()

        for order, row in enumerate(question_data, start=1):
            subject = _resolve_subject(
                db, exam_id, row.subject_code, row.subject_name, subject_cache, counters
            )
            topic = _resolve_topic(db, subject, row.topic_name, topic_cache, counters)

            item = QuestionImportItem(
                subject_id=subject.id,
                topic_id=topic.id if topic else None,
                question_type=row.question_type,
                question_text=row.question_text,
                explanation=row.explanation,
                difficulty=row.difficulty,
                marks=row.marks,
                negative_marks=row.negative_marks,
                options=row.options,
            )
            question = question_service._instantiate(  # noqa: SLF001
                item, user_id=user_id, status=QuestionStatus.DRAFT.value
            )
            question.source = row.source
            db.add(question)
            db.flush()
            db.add(
                TestQuestion(
                    test_id=test.id,
                    question_id=question.id,
                    question_order=order,
                )
            )

        db.flush()
        test.total_marks = test_repository.compute_total_marks(db, test.id)
        record_audit(
            db,
            user_id=user_id,
            module="test",
            action="import",
            entity_type="test",
            entity_id=test.id,
            new_data={
                "file": filename,
                "code": test.code,
                "questions_created": len(question_data),
                "subjects_created": counters["subjects"],
                "topics_created": counters["topics"],
            },
            request=request,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "A test with this code already exists.", code="TEST_CODE_EXISTS"
        ) from exc
    except Exception:
        db.rollback()
        raise

    return TestImportResponse(
        test_id=test.id,
        test_code=test.code,
        name=test.name,
        status=test.status,
        questions_created=len(question_data),
        subjects_created=counters["subjects"],
        topics_created=counters["topics"],
        total_marks=float(test.total_marks or 0),
    )


def build_test_import_template() -> bytes:
    """Generate the downloadable XLSX template/sample workbook."""
    return write_xlsx(
        [
            (INSTRUCTIONS_SHEET, _template_instructions()),
            (TEST_SHEET, _template_test_sheet()),
            (QUESTIONS_SHEET, _template_question_sheet()),
        ]
    )


# --------------------------------------------------------------------------- #
# Template content
# --------------------------------------------------------------------------- #
def _template_instructions() -> List[List[Any]]:
    return [
        ["Test Import - XLSX template"],
        [],
        ["How to use"],
        ["1. Select the exam in the import dialog, then upload this file."],
        ["2. Fill the 'Test' sheet: one Field / Value pair per row."],
        ["3. Fill the 'Questions' sheet: one question per row."],
        ["4. Do not rename the 'Test' or 'Questions' sheets."],
        [],
        ["Questions sheet columns"],
        ["subject_code     Code of the subject inside the chosen exam (created if missing)."],
        ["subject_name     Display name used only when the subject is created."],
        ["topic            Optional topic name (created under the subject if missing)."],
        ["question_text    The question stem (required)."],
        ["question_type    SINGLE_CHOICE (default), MULTIPLE_CHOICE, TRUE_FALSE, NUMERICAL, SUBJECTIVE."],
        ["difficulty       EASY, MEDIUM (default) or HARD."],
        ["marks            Positive marks for the question (default 4)."],
        ["negative_marks   Negative marks (default 0)."],
        ["explanation      Optional answer explanation."],
        ["source           Optional free-text reference."],
        ["option_1..6      One option per column (leave empty for NUMERICAL/SUBJECTIVE)."],
        ["correct_options  Correct option(s): numbers (1,2) or letters (A,C)."],
        [],
        ["Notes"],
        ["- Imported questions and the new test are created in DRAFT status."],
        ["- total_marks is recomputed from the imported questions."],
        ["- The import is all-or-nothing: fix every reported row and upload again."],
    ]


def _template_test_sheet() -> List[List[Any]]:
    return [
        ["Field", "Value"],
        ["name", "NEET Physics Mock Test 01"],
        ["code", "NEET-PHY-MOCK-01"],
        ["description", "Physics practice test imported from XLSX."],
        ["instructions", "Attempt all questions. Each question carries 4 marks."],
        ["duration_minutes", 180],
        ["passing_marks", 40],
        ["negative_marking_enabled", "TRUE"],
        ["negative_marks", 1],
        ["randomize_questions", "FALSE"],
        ["randomize_options", "FALSE"],
        ["max_attempts", 1],
        ["scheduled_start_at", ""],
        ["scheduled_end_at", ""],
    ]


def _template_question_sheet() -> List[List[Any]]:
    header = list(QUESTION_COLUMNS)
    sample = [
        _sample_row(
            subject_code="PHY",
            subject_name="Physics",
            topic="Kinematics",
            question_text=(
                "A body starts from rest and accelerates uniformly at 2 m/s^2. "
                "What is its velocity after 5 s?"
            ),
            question_type="SINGLE_CHOICE",
            difficulty="EASY",
            marks=4,
            negative_marks=1,
            explanation="v = u + at = 0 + 2 x 5 = 10 m/s.",
            source="NEET sample",
            options=["5 m/s", "10 m/s", "15 m/s", "20 m/s"],
            correct="2",
        ),
        _sample_row(
            subject_code="CHM",
            subject_name="Chemistry",
            topic="Chemical Bonding",
            question_text="Which of the following are noble gases?",
            question_type="MULTIPLE_CHOICE",
            difficulty="MEDIUM",
            marks=4,
            negative_marks=1,
            explanation="Helium and Neon are noble gases.",
            source="NEET sample",
            options=["Helium", "Neon", "Oxygen", "Nitrogen"],
            correct="1,2",
        ),
        _sample_row(
            subject_code="BIO",
            subject_name="Biology",
            topic="Cell Biology",
            question_text="How many chromosomes are present in a human somatic cell?",
            question_type="NUMERICAL",
            difficulty="MEDIUM",
            marks=4,
            negative_marks=0,
            explanation="A normal human somatic cell has 46 chromosomes.",
            source="NEET sample",
            options=[],
            correct="",
        ),
    ]
    return [header] + sample


def _sample_row(
    *,
    subject_code: str,
    subject_name: str,
    topic: str,
    question_text: str,
    question_type: str,
    difficulty: str,
    marks: int,
    negative_marks: int,
    explanation: str,
    source: str,
    options: List[str],
    correct: str,
) -> List[Any]:
    row: List[Any] = [
        subject_code,
        subject_name,
        topic,
        question_text,
        question_type,
        difficulty,
        marks,
        negative_marks,
        explanation,
        source,
    ]
    row.extend(options)
    row.extend([""] * (6 - len(options)))
    row.append(correct)
    return row

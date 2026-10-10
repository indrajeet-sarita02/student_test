"""Idempotent seed script for the Student Test backend (spec §21).

Creates the RBAC catalogue, demo users, exams/subjects/topics, a question bank
covering every question type, four published tests with assignments and the
runtime settings.

Usage (from the ``backend/`` directory):

    .venv/bin/python scripts/seed.py            # upsert seed data
    .venv/bin/python scripts/seed.py --reset    # TRUNCATE everything first
                                                # (asks for confirmation)

Every insert is guarded by a lookup on the entity's natural unique key
(email / code / setting_key / composite keys).  Running the script twice is a
no-op: the second run reports 0 created / everything skipped.

DEV-ONLY: every seeded account uses the password ``Admin@123``.  These
credentials exist for local/demo environments only and must be rotated before
any production deployment.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Make sure the project root (the directory that contains ``app/``) is importable
# regardless of where the script is invoked from.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select, text as sa_text  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Exam,
    Permission,
    Question,
    QuestionOption,
    Role,
    RolePermission,
    Setting,
    StudentProfile,
    Subject,
    Test,
    TestAssignment,
    TestQuestion,
    Topic,
    User,
    UserRole,
)

# ---------------------------------------------------------------------------
# DEV-ONLY credentials — documented for local/demo use, never for production.
# ---------------------------------------------------------------------------
DEV_PASSWORD = "Admin@123"

# Entities reported in the final summary (in report order).
ENTITIES: Sequence[str] = (
    "permissions",
    "roles",
    "role_permissions",
    "users",
    "user_roles",
    "student_profiles",
    "exams",
    "subjects",
    "topics",
    "questions",
    "question_options",
    "tests",
    "test_questions",
    "test_assignments",
    "settings",
)

STATS: Dict[str, Dict[str, int]] = {
    name: {"created": 0, "updated": 0, "skipped": 0} for name in ENTITIES
}


# ---------------------------------------------------------------------------
# Generic guarded insert helpers
# ---------------------------------------------------------------------------
def _equal(current: Any, wanted: Any) -> bool:
    """Compare a stored value with a seed value across numeric wrapper types."""
    if current is None or wanted is None:
        return current is None and wanted is None
    if isinstance(current, (int, float, Decimal)) and isinstance(wanted, (int, float, Decimal)):
        return float(current) == float(wanted)
    return current == wanted


def upsert(
    session,
    model,
    key: Dict[str, Any],
    values: Dict[str, Any],
    entity: str,
    ignore: Sequence[str] = (),
):
    """Look up ``model`` by ``key``; insert when missing, else refresh fields.

    ``ignore`` lists value fields that must not be compared (e.g. volatile
    timestamps or hashed passwords) so an unchanged row stays a "skip".
    Returns ``(row, created)``.
    """
    stmt = select(model).where(*(getattr(model, k) == v for k, v in key.items()))
    row = session.execute(stmt).scalar_one_or_none()
    if row is None:
        row = model(**{**key, **values})  # type: ignore[arg-type]
        session.add(row)
        session.flush()
        STATS[entity]["created"] += 1
        return row, True

    changed = False
    for field, wanted in values.items():
        if field in ignore:
            continue
        current = getattr(row, field)
        if not _equal(current, wanted):
            setattr(row, field, wanted)
            changed = True
    if changed:
        STATS[entity]["updated"] += 1
    else:
        STATS[entity]["skipped"] += 1
    return row, False


def link_row(session, model, key: Dict[str, Any], entity: str, **extra: Any) -> None:
    """Guard an association-table row by its unique key."""
    stmt = select(model).where(*(getattr(model, k) == v for k, v in key.items()))
    row = session.execute(stmt).scalar_one_or_none()
    if row is None:
        session.add(model(**{**key, **extra}))  # type: ignore[arg-type]
        session.flush()
        STATS[entity]["created"] += 1
    else:
        STATS[entity]["skipped"] += 1


# ---------------------------------------------------------------------------
# Seed content (spec §21)
# ---------------------------------------------------------------------------
# (code, human-readable name) — module/action are derived from the code.
PERMISSION_SPECS: Sequence[Tuple[str, str]] = (
    ("user.view", "View users"),
    ("user.create", "Create users"),
    ("user.update", "Update users"),
    ("user.delete", "Delete users"),
    ("role.view", "View roles"),
    ("role.create", "Create roles"),
    ("role.update", "Update roles"),
    ("role.delete", "Delete roles"),
    ("permission.view", "View permissions"),
    ("exam.view", "View exams"),
    ("exam.create", "Create exams"),
    ("exam.update", "Update exams"),
    ("exam.delete", "Delete exams"),
    ("exam.publish", "Publish exams"),
    ("question.view", "View questions"),
    ("question.create", "Create questions"),
    ("question.update", "Update questions"),
    ("question.delete", "Delete questions"),
    ("question.publish", "Publish questions"),
    ("test.view", "View tests"),
    ("test.create", "Create tests"),
    ("test.update", "Update tests"),
    ("test.delete", "Delete tests"),
    ("test.publish", "Publish tests"),
    ("test.assign", "Assign tests"),  # canonical code test.assign → action "assign"
    ("attempt.view", "View attempts"),
    ("result.view", "View results"),
    ("result.publish", "Publish results"),
    ("result.export", "Export results"),
    ("report.view", "View reports"),
    ("notification.view", "View notifications"),
    ("notification.create", "Create notifications"),
    ("audit.view", "View audit logs"),
    ("settings.view", "View settings"),
    ("settings.update", "Update settings"),
)
ALL_PERMISSION_CODES: List[str] = [code for code, _ in PERMISSION_SPECS]

_EXAM_ALL = [f"exam.{a}" for a in ("view", "create", "update", "delete", "publish")]
_QUESTION_ALL = [f"question.{a}" for a in ("view", "create", "update", "delete", "publish")]
_TEST_ALL = [f"test.{a}" for a in ("view", "create", "update", "delete", "publish", "assign")]
_TEST_WRITE = ["test.view", "test.create", "test.update", "test.publish", "test.assign"]

# code -> (display name, description, is_system_role)
ROLES: Dict[str, Tuple[str, str, bool]] = {
    "SUPER_ADMIN": ("Super Admin", "Full unrestricted access to every module.", True),
    "ADMIN": ("Administrator", "Administrative access to every module.", False),
    "CONTENT_MANAGER": (
        "Content Manager",
        "Manages users (read), exams, questions and tests.",
        False,
    ),
    "EXAMINER": (
        "Examiner",
        "Creates exams/questions/tests and publishes results.",
        False,
    ),
    "REPORT_VIEWER": (
        "Report Viewer",
        "Read-only access to reports, results and audit logs.",
        False,
    ),
    "STUDENT": ("Student", "Takes assigned tests (ownership-based student APIs).", False),
}

ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "SUPER_ADMIN": list(ALL_PERMISSION_CODES),
    "ADMIN": list(ALL_PERMISSION_CODES),
    "CONTENT_MANAGER": [
        "user.view",
        "role.view",
        "permission.view",
        *_EXAM_ALL,
        *_QUESTION_ALL,
        *_TEST_WRITE,
        "attempt.view",
        "result.view",
        "report.view",
        "notification.view",
        "notification.create",
        "audit.view",
    ],
    "EXAMINER": [
        "user.view",
        "role.view",
        "permission.view",
        "exam.view",
        "exam.create",
        "exam.update",
        *_QUESTION_ALL,
        *_TEST_ALL,
        "attempt.view",
        "result.view",
        "result.publish",
        "result.export",
        "report.view",
        "notification.view",
    ],
    "REPORT_VIEWER": [
        "user.view",
        "role.view",
        "permission.view",
        "exam.view",
        "question.view",
        "test.view",
        "attempt.view",
        "result.view",
        "result.export",
        "report.view",
        "audit.view",
    ],
    "STUDENT": [],  # student APIs are ownership-based; no RBAC codes required
}

# username, email, first name, last name, role code
USERS: Sequence[Tuple[str, str, str, str, str]] = (
    ("superadmin", "superadmin@example.com", "Super", "Admin", "SUPER_ADMIN"),
    ("admin", "admin@example.com", "Admin", "User", "ADMIN"),
    ("teacher", "teacher@example.com", "Exam", "Teacher", "EXAMINER"),
    ("content", "content@example.com", "Content", "Manager", "CONTENT_MANAGER"),
    ("student", "student@example.com", "Student", "One", "STUDENT"),
    ("report", "report@example.com", "Report", "Viewer", "REPORT_VIEWER"),
    ("student2", "student2@example.com", "Student", "Two", "STUDENT"),
)

# email -> (student_code, gender, institution, class_name, roll_number)
STUDENT_PROFILES: Dict[str, Tuple[str, str, str, str, str]] = {
    "student@example.com": ("STU-001", "FEMALE", "Demo College", "Class XII", "1"),
    "student2@example.com": ("STU-002", "MALE", "Demo College", "Class XII", "2"),
}

# code, name, exam_type, duration_minutes, passing_percentage, description
EXAMS: Sequence[Tuple[str, str, str, int, float, str]] = (
    ("NEET", "National Eligibility cum Entrance Test", "NEET", 180, 50.0,
     "Undergraduate medical entrance examination."),
    ("JEE", "Joint Entrance Examination", "JEE", 180, 40.0,
     "Undergraduate engineering entrance examination."),
    ("UPSC", "UPSC Civil Services Examination", "UPSC", 180, 33.0,
     "Civil services (IAS/IPS) examination."),
    ("SSC", "Staff Selection Commission Examination", "SSC", 60, 35.0,
     "Staff selection combined graduate level examination."),
    ("CUSTOM", "Custom Practice Exam", "CUSTOM", 60, 40.0,
     "In-house custom practice examination."),
)

# exam code -> [(subject name, subject code, sort_order)]
SUBJECTS: Dict[str, Sequence[Tuple[str, str, int]]] = {
    "NEET": [("Physics", "PHY", 1), ("Chemistry", "CHM", 2), ("Biology", "BIO", 3)],
    "JEE": [("Physics", "PHY", 1), ("Chemistry", "CHM", 2), ("Mathematics", "MAT", 3)],
    "UPSC": [("General Studies", "GS", 1), ("English", "ENG", 2)],
    "SSC": [("General Studies", "GS", 1), ("English", "ENG", 2)],
    "CUSTOM": [("General Studies", "GS", 1)],
}

# (exam code, subject code) -> topic names
TOPICS: Dict[Tuple[str, str], Sequence[str]] = {
    ("NEET", "PHY"): ("Kinematics", "Laws of Motion", "Work Energy Power"),
    ("NEET", "CHM"): ("Atomic Structure", "Chemical Bonding", "Thermodynamics"),
    ("NEET", "BIO"): ("Cell Biology", "Human Physiology", "Genetics"),
    ("JEE", "PHY"): ("Mechanics", "Electrodynamics"),
    ("JEE", "CHM"): ("Physical Chemistry", "Organic Chemistry"),
    ("JEE", "MAT"): ("Algebra", "Calculus", "Coordinate Geometry"),
    ("UPSC", "GS"): ("Indian Polity", "Modern History"),
    ("UPSC", "ENG"): ("Reading Comprehension", "Grammar"),
    ("SSC", "GS"): ("History", "Geography", "Sports"),
    ("SSC", "ENG"): ("Vocabulary", "Grammar"),
    ("CUSTOM", "GS"): ("General Knowledge", "Current Affairs"),
}

_Q_MARKS = 4.0
_Q_NEGATIVE = 1.0

# key, exam, subject, topic, type, difficulty, text, explanation, options
QUESTIONS: Sequence[Dict[str, Any]] = (
    # ---- NEET Physics (4) ---------------------------------------------------
    dict(
        key="NEET-PHY-Q01", exam="NEET", subject="PHY", topic="Kinematics",
        type="SINGLE_CHOICE", difficulty="EASY",
        text="A car starts from rest and accelerates uniformly at 2 m/s^2. "
             "What is its velocity after 5 seconds?",
        explanation="Using v = u + at with u = 0: v = 0 + 2 x 5 = 10 m/s.",
        options=[("5 m/s", False), ("10 m/s", True), ("15 m/s", False), ("20 m/s", False)],
    ),
    dict(
        key="NEET-PHY-Q02", exam="NEET", subject="PHY", topic="Laws of Motion",
        type="NUMERICAL", difficulty="MEDIUM",
        text="A horizontal force of 10 N acts on a 2 kg block initially at rest on a "
             "frictionless surface. What distance (in metres) does the block cover in 4 seconds?",
        explanation="a = F/m = 10/2 = 5 m/s^2. s = 1/2 a t^2 = 1/2 x 5 x 4^2 = 40 m.",
        options=[("40", True), ("80", False)],
    ),
    dict(
        key="NEET-PHY-Q03", exam="NEET", subject="PHY", topic="Laws of Motion",
        type="TRUE_FALSE", difficulty="EASY",
        text="Newton's second law states that the rate of change of momentum of a body is "
             "directly proportional to the applied force.",
        explanation="F = dp/dt is the mathematical statement of Newton's second law.",
        options=[("TRUE", True), ("FALSE", False)],
    ),
    dict(
        key="NEET-PHY-Q04", exam="NEET", subject="PHY", topic="Work Energy Power",
        type="MULTIPLE_CHOICE", difficulty="MEDIUM",
        text="Which of the following quantities are scalars?",
        explanation="Work and kinetic energy have magnitude only, while momentum and "
                    "impulse are vectors that also have direction.",
        options=[("Work", True), ("Kinetic energy", True), ("Momentum", False),
                 ("Impulse", False)],
    ),
    # ---- NEET Chemistry (2) -------------------------------------------------
    dict(
        key="NEET-CHM-Q01", exam="NEET", subject="CHM", topic="Atomic Structure",
        type="SINGLE_CHOICE", difficulty="EASY",
        text="What is the maximum number of electrons that can occupy a single atomic orbital?",
        explanation="By Pauli's exclusion principle an orbital accommodates at most two "
                    "electrons with opposite spins.",
        options=[("1", False), ("2", True), ("4", False), ("8", False)],
    ),
    dict(
        key="NEET-CHM-Q02", exam="NEET", subject="CHM", topic="Chemical Bonding",
        type="MULTIPLE_CHOICE", difficulty="HARD",
        text="Which of the following molecules have a bond order of 3?",
        explanation="N2 and CO are isoelectronic (14 electrons) and both have a bond order "
                    "of 3; O2 has a bond order of 2 and H2 a bond order of 1.",
        options=[("N2", True), ("CO", True), ("O2", False), ("H2", False)],
    ),
    # ---- NEET Biology (2) --------------------------------------------------
    dict(
        key="NEET-BIO-Q01", exam="NEET", subject="BIO", topic="Cell Biology",
        type="TRUE_FALSE", difficulty="EASY",
        text="Mitochondria are the site of aerobic respiration in eukaryotic cells.",
        explanation="Glycolysis occurs in the cytoplasm, but the Krebs cycle and oxidative "
                    "phosphorylation take place inside the mitochondria.",
        options=[("TRUE", True), ("FALSE", False)],
    ),
    dict(
        key="NEET-BIO-Q02", exam="NEET", subject="BIO", topic="Genetics",
        type="SINGLE_CHOICE", difficulty="MEDIUM",
        text="Mendel's law of independent assortment applies to genes that are:",
        explanation="Genes on different chromosome pairs segregate independently during "
                    "anaphase I of meiosis, which is the basis of independent assortment.",
        options=[
            ("on the same chromosome", False),
            ("on different, non-homologous chromosomes", True),
            ("located only on the X chromosome", False),
            ("encoded by mitochondrial DNA", False),
        ],
    ),
    # ---- JEE Mathematics (4) -----------------------------------------------
    dict(
        key="JEE-MAT-Q01", exam="JEE", subject="MAT", topic="Algebra",
        type="SINGLE_CHOICE", difficulty="EASY",
        text="If alpha and beta are the roots of x^2 - 5x + 6 = 0, what is alpha + beta?",
        explanation="For ax^2 + bx + c the sum of the roots is -b/a = -(-5)/1 = 5.",
        options=[("5", True), ("6", False), ("-5", False), ("11", False)],
    ),
    dict(
        key="JEE-MAT-Q02", exam="JEE", subject="MAT", topic="Calculus",
        type="NUMERICAL", difficulty="MEDIUM",
        text="Evaluate the definite integral of 3x^2 dx from 0 to 2.",
        explanation="The antiderivative of 3x^2 is x^3, so [x^3] from 0 to 2 = 8 - 0 = 8.",
        options=[("8", True), ("4", False)],
    ),
    dict(
        key="JEE-MAT-Q03", exam="JEE", subject="MAT", topic="Coordinate Geometry",
        type="MULTIPLE_CHOICE", difficulty="MEDIUM",
        text="Which of the following points satisfy the linear equation 3x - 2y = 4?",
        explanation="3(2) - 2(1) = 4 and 3(0) - 2(-2) = 4, while 3(1) - 2(1) = 1 and "
                    "3(3) - 2(2) = 5.",
        options=[("(2, 1)", True), ("(0, -2)", True), ("(1, 1)", False), ("(3, 2)", False)],
    ),
    dict(
        key="JEE-MAT-Q04", exam="JEE", subject="MAT", topic="Calculus",
        type="TRUE_FALSE", difficulty="HARD",
        text="If f is continuous on [a, b], differentiable on (a, b) and f'(x) > 0 for "
             "every x in (a, b), then f is strictly increasing on [a, b].",
        explanation="By the Mean Value Theorem f(b) - f(a) = f'(c)(b - a) > 0 for any "
                    "b > a, so f is strictly increasing on the interval.",
        options=[("TRUE", True), ("FALSE", False)],
    ),
    # ---- SSC General Knowledge (4) -----------------------------------------
    dict(
        key="SSC-GS-Q01", exam="SSC", subject="GS", topic="History",
        type="SINGLE_CHOICE", difficulty="EASY",
        text="The Quit India Movement was launched in which year?",
        explanation="Mahatma Gandhi gave the 'Do or Die' call on 8 August 1942, launching "
                    "the Quit India Movement.",
        options=[("1930", False), ("1942", True), ("1935", False), ("1947", False)],
    ),
    dict(
        key="SSC-GS-Q02", exam="SSC", subject="GS", topic="Geography",
        type="SINGLE_CHOICE", difficulty="EASY",
        text="Which is the longest river of India?",
        explanation="The Ganga flows about 2,525 km through India, making it the longest "
                    "river of the country; the Godavari is the second longest.",
        options=[("Godavari", False), ("Ganga", True), ("Yamuna", False),
                 ("Brahmaputra", False)],
    ),
    dict(
        key="SSC-GS-Q03", exam="SSC", subject="GS", topic="Geography",
        type="TRUE_FALSE", difficulty="MEDIUM",
        text="The Tropic of Cancer passes through eight Indian states.",
        explanation="It passes through Gujarat, Rajasthan, Madhya Pradesh, Chhattisgarh, "
                    "Jharkhand, West Bengal, Tripura and Mizoram.",
        options=[("TRUE", True), ("FALSE", False)],
    ),
    dict(
        key="SSC-GS-Q04", exam="SSC", subject="GS", topic="Sports",
        type="NUMERICAL", difficulty="EASY",
        text="How many players from each team are on the court at the start of a "
             "kabaddi match?",
        explanation="A kabaddi squad has 12 players, of which 7 are on the court at any "
                    "given time.",
        options=[("7", True), ("11", False)],
    ),
)

# code, name, exam code, duration, randomize, description, instructions, question keys
TESTS: Sequence[Dict[str, Any]] = (
    dict(
        code="NEET-PHY-PT01", name="NEET Physics Practice Test", exam="NEET",
        duration=60, randomize=False,
        description="Topic-wise physics practice test for NEET aspirants.",
        instructions="Duration: 60 minutes. Each question carries 4 marks. "
                     "Negative marking: 1 mark is deducted for every wrong answer.",
        question_keys=["NEET-PHY-Q01", "NEET-PHY-Q02", "NEET-PHY-Q03", "NEET-PHY-Q04"],
    ),
    dict(
        code="NEET-FULL-MT01", name="NEET Full Mock Test", exam="NEET",
        duration=180, randomize=True,
        description="Full-length NEET mock test covering Physics, Chemistry and Biology.",
        instructions="Duration: 180 minutes. Question order is randomised. "
                     "Negative marking: 1 mark is deducted for every wrong answer.",
        question_keys=[
            "NEET-PHY-Q01", "NEET-PHY-Q02", "NEET-PHY-Q03", "NEET-PHY-Q04",
            "NEET-CHM-Q01", "NEET-CHM-Q02", "NEET-BIO-Q01", "NEET-BIO-Q02",
        ],
    ),
    dict(
        code="JEE-MATH-PT01", name="JEE Mathematics Practice Test", exam="JEE",
        duration=60, randomize=False,
        description="Practice test for the JEE Mathematics syllabus.",
        instructions="Duration: 60 minutes. Each question carries 4 marks. "
                     "Negative marking: 1 mark is deducted for every wrong answer.",
        question_keys=["JEE-MAT-Q01", "JEE-MAT-Q02", "JEE-MAT-Q03", "JEE-MAT-Q04"],
    ),
    dict(
        code="SSC-GK-T01", name="SSC General Knowledge Test", exam="SSC",
        duration=30, randomize=False,
        description="General knowledge test for SSC aspirants.",
        instructions="Duration: 30 minutes. Each question carries 4 marks. "
                     "Negative marking: 1 mark is deducted for every wrong answer.",
        question_keys=["SSC-GS-Q01", "SSC-GS-Q02", "SSC-GS-Q03", "SSC-GS-Q04"],
    ),
)

# setting key, value, description, is_public
SETTINGS: Sequence[Tuple[str, str, str, bool]] = (
    ("site_name", "Student Test Portal", "Public site title shown in the UI.", True),
    ("default_test_duration_minutes", "180",
     "Default duration (minutes) pre-filled when creating a test.", True),
    ("enable_negative_marking", "true",
     "Whether negative marking is enabled by default for new tests.", True),
    ("support_email", "support@example.com", "Public support contact email.", True),
    ("maintenance_mode", "false",
     "When true the portal rejects non-admin requests.", False),
)

ASSIGNMENT_STUDENTS: Sequence[str] = ("student@example.com", "student2@example.com")


# ---------------------------------------------------------------------------
# Seed sections
# ---------------------------------------------------------------------------
def seed_permissions(session) -> None:
    for code, name in PERMISSION_SPECS:
        module, action = code.split(".", 1)
        upsert(
            session,
            Permission,
            key={"code": code},
            values={"name": name, "module": module, "action": action,
                    "description": name},
            entity="permissions",
        )
    session.commit()


def seed_roles(session) -> None:
    permission_ids = {
        p.code: p.id for p in session.execute(select(Permission)).scalars()
    }
    for code, (name, description, is_system) in ROLES.items():
        role, _ = upsert(
            session,
            Role,
            key={"code": code},
            values={"name": name, "description": description,
                    "is_system_role": is_system, "is_active": True},
            entity="roles",
        )
        for perm_code in ROLE_PERMISSIONS.get(code, []):
            link_row(
                session,
                RolePermission,
                key={"role_id": role.id, "permission_id": permission_ids[perm_code]},
                entity="role_permissions",
            )
    session.commit()


def seed_users(session) -> Dict[str, int]:
    role_ids = {r.code: r.id for r in session.execute(select(Role)).scalars()}
    user_ids: Dict[str, int] = {}

    for username, email, first_name, last_name, role_code in USERS:
        stmt = select(User).where(User.email == email)
        user = session.execute(stmt).scalar_one_or_none()
        if user is None:
            # DEV-ONLY password: Admin@123 (see module docstring).
            user = User(
                username=username,
                email=email,
                password_hash=hash_password(DEV_PASSWORD),
                first_name=first_name,
                last_name=last_name,
                status="ACTIVE",
                is_verified=True,
            )
            session.add(user)
            session.flush()
            STATS["users"]["created"] += 1
        else:
            changed = False
            for field, wanted in (
                ("username", username),
                ("first_name", first_name),
                ("last_name", last_name),
                ("status", "ACTIVE"),
                ("is_verified", True),
            ):
                if not _equal(getattr(user, field), wanted):
                    setattr(user, field, wanted)
                    changed = True
            STATS["users"]["updated" if changed else "skipped"] += 1

        user_ids[email] = user.id
        link_row(
            session,
            UserRole,
            key={"user_id": user.id, "role_id": role_ids[role_code]},
            entity="user_roles",
        )

    # Student profiles — ``class_name`` is a plain column on student_profiles.
    for email, (student_code, gender, institution, class_name, roll_number) in (
        STUDENT_PROFILES.items()
    ):
        upsert(
            session,
            StudentProfile,
            key={"user_id": user_ids[email]},
            values={
                "student_code": student_code,
                "gender": gender,
                "institution": institution,
                "class_name": class_name,
                "roll_number": roll_number,
            },
            entity="student_profiles",
        )
    session.commit()
    return user_ids


def seed_exams(session, owner_id: int) -> Dict[str, int]:
    exam_ids: Dict[str, int] = {}
    for code, name, exam_type, duration, passing, description in EXAMS:
        exam, _ = upsert(
            session,
            Exam,
            key={"code": code},
            values={
                "name": name,
                "description": description,
                "exam_type": exam_type,
                "status": "PUBLISHED",
                "duration_minutes": duration,
                "passing_percentage": passing,
                "is_active": True,
                "created_by": owner_id,
                "updated_by": owner_id,
            },
            entity="exams",
        )
        exam_ids[code] = exam.id
    session.commit()
    return exam_ids


def seed_subjects(session, exam_ids: Dict[str, int]) -> Dict[Tuple[int, str], int]:
    subject_ids: Dict[Tuple[int, str], int] = {}
    for exam_code, rows in SUBJECTS.items():
        for name, code, sort_order in rows:
            subject, _ = upsert(
                session,
                Subject,
                key={"exam_id": exam_ids[exam_code], "code": code},
                values={"name": name, "description": f"{name} for {exam_code}",
                        "sort_order": sort_order, "is_active": True},
                entity="subjects",
            )
            subject_ids[(exam_ids[exam_code], code)] = subject.id
    session.commit()
    return subject_ids


def seed_topics(session, subject_ids: Dict[Tuple[int, str], int]) -> Dict[Tuple[int, str], int]:
    topic_ids: Dict[Tuple[int, str], int] = {}
    for (exam_code, subject_code), names in TOPICS.items():
        s_key = (exam_ids_cache[exam_code], subject_code)
        subject_id = subject_ids[s_key]
        for order, name in enumerate(names, start=1):
            topic, _ = upsert(
                session,
                Topic,
                key={"subject_id": subject_id, "name": name},
                values={"description": f"{name} ({exam_code} {subject_code})",
                        "sort_order": order, "is_active": True},
                entity="topics",
            )
            topic_ids[(subject_id, name)] = topic.id
    session.commit()
    return topic_ids


def seed_questions(session, owner_id: int, subject_ids, topic_ids) -> Dict[str, int]:
    question_ids: Dict[str, int] = {}
    for spec in QUESTIONS:
        subject_id = subject_ids[(exam_ids_cache[spec["exam"]], spec["subject"])]
        topic_id = topic_ids[(subject_id, spec["topic"])]
        question, _ = upsert(
            session,
            Question,
            key={"question_text": spec["text"]},
            values={
                "subject_id": subject_id,
                "topic_id": topic_id,
                "question_type": spec["type"],
                "explanation": spec["explanation"],
                "difficulty": spec["difficulty"],
                "marks": _Q_MARKS,
                "negative_marks": _Q_NEGATIVE,
                "status": "PUBLISHED",
                "source": "seed",
                "is_active": True,
                "created_by": owner_id,
                "updated_by": owner_id,
            },
            entity="questions",
        )
        question_ids[spec["key"]] = question.id
        for order, (text, is_correct) in enumerate(spec["options"], start=1):
            upsert(
                session,
                QuestionOption,
                key={"question_id": question.id, "option_order": order},
                values={"option_text": text, "is_correct": is_correct,
                        "is_active": True},
                entity="question_options",
            )
    session.commit()
    return question_ids


def seed_tests(session, exam_ids, question_ids, user_ids) -> None:
    now = datetime.now(timezone.utc)
    available_from = now - timedelta(days=1)
    available_until = now + timedelta(days=30)

    for spec in TESTS:
        marks_by_key = {q["key"]: q for q in QUESTIONS}
        total_marks = float(sum(
            _Q_MARKS for _ in spec["question_keys"]
        ))
        passing_marks = round(total_marks * 0.4, 2)

        test, _ = upsert(
            session,
            Test,
            key={"code": spec["code"]},
            values={
                "exam_id": exam_ids[spec["exam"]],
                "name": spec["name"],
                "description": spec["description"],
                "instructions": spec["instructions"],
                "duration_minutes": spec["duration"],
                "total_marks": total_marks,
                "passing_marks": passing_marks,
                "negative_marking_enabled": True,
                "negative_marks": 1.0,
                "randomize_questions": spec["randomize"],
                "randomize_options": False,
                "max_attempts": 2,
                "status": "PUBLISHED",
                "created_by": user_ids["superadmin@example.com"],
                "updated_by": user_ids["superadmin@example.com"],
            },
            entity="tests",
        )
        del marks_by_key  # marks are uniform (4.0) — see _Q_MARKS

        for order, q_key in enumerate(spec["question_keys"], start=1):
            link_row(
                session,
                TestQuestion,
                key={"test_id": test.id, "question_id": question_ids[q_key]},
                entity="test_questions",
                question_order=order,
            )

        for email in ASSIGNMENT_STUDENTS:
            upsert(
                session,
                TestAssignment,
                key={"test_id": test.id, "student_id": user_ids[email]},
                values={
                    "assigned_at": now,
                    "available_from": available_from,
                    "available_until": available_until,
                    "max_attempts": 2,
                    "status": "ASSIGNED",
                },
                entity="test_assignments",
                # volatile timestamps: never re-compared, so re-runs stay skips
                ignore=("assigned_at", "available_from", "available_until"),
            )
    session.commit()


def seed_settings(session, owner_id: int) -> None:
    for key, value, description, is_public in SETTINGS:
        upsert(
            session,
            Setting,
            key={"setting_key": key},
            values={"setting_value": value, "description": description,
                    "is_public": is_public, "updated_by": owner_id},
            entity="settings",
        )
    session.commit()


# Cache of exam ids used by seed_topics/seed_questions (populated in run_seed).
exam_ids_cache: Dict[str, int] = {}


def run_seed(session) -> Dict[str, int]:
    print("=" * 64)
    print("Student Test backend — seed data (spec §21)")
    print(f"DEV-ONLY: all demo accounts use the password '{DEV_PASSWORD}'.")
    print("=" * 64)

    seed_permissions(session)
    seed_roles(session)
    user_ids = seed_users(session)
    exam_ids = seed_exams(session, user_ids["superadmin@example.com"])
    exam_ids_cache.clear()
    exam_ids_cache.update(exam_ids)
    subject_ids = seed_subjects(session, exam_ids)
    topic_ids = seed_topics(session, subject_ids)
    question_ids = seed_questions(session, user_ids["superadmin@example.com"],
                                  subject_ids, topic_ids)
    seed_tests(session, exam_ids, question_ids, user_ids)
    seed_settings(session, user_ids["superadmin@example.com"])
    return STATS


def reset_database(session) -> None:
    tables = [t.name for t in Base.metadata.sorted_tables if t.name != "alembic_version"]
    answer = input(
        f"\nWARNING: --reset will TRUNCATE {len(tables)} tables "
        f"(RESTART IDENTITY CASCADE) and delete ALL existing data.\n"
        f"Type 'yes' to continue: "
    ).strip().lower()
    if answer not in {"y", "yes"}:
        print("Reset cancelled — nothing was truncated.")
        sys.exit(1)
    quoted = ", ".join(f'"{t}"' for t in tables)
    session.execute(sa_text(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE"))
    session.commit()
    print(f"Truncated {len(tables)} tables (alembic_version kept).")


def print_summary() -> None:
    print()
    print("=" * 64)
    print(f"{'SEED SUMMARY':^64}")
    print("=" * 64)
    print(f"{'entity':<24}{'created':>10}{'updated':>10}{'skipped':>10}")
    print("-" * 64)
    totals = {"created": 0, "updated": 0, "skipped": 0}
    for entity in ENTITIES:
        row = STATS[entity]
        for k in totals:
            totals[k] += row[k]
        print(f"{entity:<24}{row['created']:>10}{row['updated']:>10}{row['skipped']:>10}")
    print("-" * 64)
    print(f"{'TOTAL':<24}{totals['created']:>10}{totals['updated']:>10}{totals['skipped']:>10}")
    print("=" * 64)
    if totals["created"] == 0 and totals["updated"] == 0:
        print("Idempotent re-run: nothing was created or changed — all rows skipped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Student Test database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="TRUNCATE all tables (cascade) before seeding — asks for confirmation.",
    )
    args = parser.parse_args()

    session = SessionLocal()
    try:
        if args.reset:
            reset_database(session)
        run_seed(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print_summary()


if __name__ == "__main__":
    main()

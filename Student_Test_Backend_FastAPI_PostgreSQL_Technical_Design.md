# Student Test Application — Backend Technical Design & Development Specification

## 1. Document Overview

| Item | Specification |
|---|---|
| Backend Framework | FastAPI |
| Language | Python 3.x |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Database Migration | Alembic |
| API Style | RESTful JSON API |
| API Documentation | OpenAPI / Swagger UI |
| Authentication | JWT |
| Authorization | Role-Based Access Control (RBAC) |
| Primary Keys | Numeric `BIGINT`/`INTEGER` IDs |
| Cache | **Not required** |
| Validation | Pydantic |
| Password Hashing | Argon2id or bcrypt |
| Testing | Pytest + HTTPX |
| Configuration | Environment variables / `.env` |
| Containerization | Docker recommended |

---

## 2. Architecture Objective

The backend will provide a secure REST API consumed exclusively by the Next.js frontend.

Core principles:

- API-first architecture.
- Clear separation between routers, services, repositories/data access, schemas and ORM models.
- PostgreSQL as the system of record.
- SQLAlchemy 2.x ORM.
- Alembic for schema migrations.
- Numeric primary keys for all business entities.
- JWT access/refresh-token authentication.
- Server-side authorization for every protected operation.
- No application cache or Redis dependency in the initial version.
- Swagger/OpenAPI documentation for every API.
- Centralized exception handling and validation.
- Auditability of important administrative operations.
- Historical test attempts and results must remain consistent.

---

## 3. High-Level Architecture

```text
                    +----------------------+
                    |      Next.js UI      |
                    +----------+-----------+
                               |
                         HTTPS / JSON
                               |
                    +----------v-----------+
                    |      FastAPI API     |
                    +----------+-----------+
                               |
          +--------------------+--------------------+
          |                    |                    |
   +------v------+      +------v------+      +------v------+
   | Auth / RBAC |      |  Services   |      |   Reports   |
   +-------------+      +------+------+      +-------------+
                               |
                        +------v------+
                        | Repositories |
                        +------+------+
                               |
                        +------v------+
                        | SQLAlchemy  |
                        |    ORM      |
                        +------+------+
                               |
                        +------v------+
                        | PostgreSQL  |
                        +-------------+
```

---

## 4. Recommended Backend Project Structure

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── jwt.py
│   │   ├── permissions.py
│   │   └── exceptions.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── seed.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── permission.py
│   │   ├── exam.py
│   │   ├── subject.py
│   │   ├── topic.py
│   │   ├── question.py
│   │   ├── test.py
│   │   ├── assignment.py
│   │   ├── attempt.py
│   │   ├── result.py
│   │   ├── notification.py
│   │   ├── audit_log.py
│   │   └── setting.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── exam.py
│   │   ├── subject.py
│   │   ├── topic.py
│   │   ├── question.py
│   │   ├── test.py
│   │   ├── attempt.py
│   │   ├── result.py
│   │   └── common.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── exam_repository.py
│   │   ├── question_repository.py
│   │   ├── test_repository.py
│   │   └── attempt_repository.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── exam_service.py
│   │   ├── question_service.py
│   │   ├── test_service.py
│   │   ├── attempt_service.py
│   │   ├── scoring_service.py
│   │   ├── report_service.py
│   │   └── notification_service.py
│   │
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── roles.py
│   │       ├── permissions.py
│   │       ├── exams.py
│   │       ├── subjects.py
│   │       ├── topics.py
│   │       ├── questions.py
│   │       ├── tests.py
│   │       ├── assignments.py
│   │       ├── attempts.py
│   │       ├── results.py
│   │       ├── reports.py
│   │       ├── notifications.py
│   │       ├── audit_logs.py
│   │       └── settings.py
│   │
│   └── utils/
│       ├── pagination.py
│       ├── datetime.py
│       └── enums.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── tests/
├── scripts/
│   └── seed.py
├── requirements.txt
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 5. Technology Stack

### Required

```text
Python
FastAPI
Uvicorn
Pydantic
Pydantic Settings
SQLAlchemy 2.x
psycopg
Alembic
python-jose or PyJWT
pwdlib / Argon2id or bcrypt
python-multipart
email-validator
pytest
httpx
```

### Example `requirements.txt`

```text
fastapi
uvicorn[standard]
sqlalchemy
psycopg[binary]
alembic
pydantic
pydantic-settings
pyjwt
pwdlib[argon2]
python-multipart
email-validator
pytest
httpx
```

Do not add Redis or another cache library unless a future requirement explicitly introduces caching.

---

# 6. Configuration

Example `.env.example`:

```env
APP_NAME=Student Test API
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/student_test

JWT_SECRET_KEY=CHANGE_ME
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

CORS_ORIGINS=http://localhost:3000

PASSWORD_HASH_ALGORITHM=argon2
```

Production secrets must never be committed to Git.

---

# 7. Database Standards

## 7.1 Primary Key Standard

All main tables use numeric IDs.

Recommended:

```sql
id BIGSERIAL PRIMARY KEY
```

or SQLAlchemy:

```python
id: Mapped[int] = mapped_column(
    BigInteger,
    primary_key=True,
    autoincrement=True
)
```

Do not use UUID as the primary key for this application.

## 7.2 Standard Audit Columns

Most business tables should contain:

```text
id
created_at
updated_at
created_by
updated_by
is_active
```

Where soft deletion is required:

```text
deleted_at
```

Avoid physically deleting historical entities such as questions referenced by completed attempts.

---

# 8. Core Database Entities

## 8.1 users

```text
id
username
email
password_hash
first_name
last_name
mobile
status
is_verified
last_login_at
created_at
updated_at
```

Constraints:

- `email` unique.
- `username` unique.
- Password must never be stored in plain text.

## 8.2 student_profiles

```text
id
user_id FK users.id
student_code
date_of_birth
gender
institution
class_name
roll_number
created_at
updated_at
```

## 8.3 roles

```text
id
name
code
description
is_system_role
is_active
created_at
updated_at
```

## 8.4 permissions

```text
id
name
code
module
action
description
```

Example:

```text
user.view
user.create
user.update
user.delete
exam.view
exam.create
exam.update
exam.delete
exam.publish
question.view
question.create
question.update
question.delete
question.publish
test.view
test.create
test.update
test.publish
attempt.view
result.view
result.export
report.view
report.export
```

## 8.5 user_roles

```text
id
user_id
role_id
```

## 8.6 role_permissions

```text
id
role_id
permission_id
```

## 8.7 exams

```text
id
name
code
description
exam_type
status
duration_minutes
passing_percentage
start_at
end_at
created_by
updated_by
created_at
updated_at
```

## 8.8 subjects

```text
id
exam_id
name
code
description
sort_order
is_active
```

## 8.9 topics

```text
id
subject_id
parent_topic_id nullable
name
description
sort_order
is_active
```

## 8.10 questions

```text
id
subject_id
topic_id nullable
question_type
question_text
explanation
difficulty
marks
negative_marks
status
source
tags (JSONB array of free-form labels)
created_by
updated_by
created_at
updated_at
```

`tags` is used to label and filter the question bank (`?tag=` on the listing).

## 8.11 question_options

```text
id
question_id
option_text
option_order
is_correct
```

For security, `is_correct` must never be exposed to students through test-taking APIs.

## 8.12 tests

```text
id
exam_id
name
code
description
instructions
duration_minutes
total_marks
passing_marks
negative_marking_enabled
negative_marks
randomize_questions
randomize_options
max_attempts
status
scheduled_start_at
scheduled_end_at
created_by
updated_by
created_at
updated_at
```

## 8.13 test_questions

```text
id
test_id
question_id
question_order
marks_override nullable
negative_marks_override nullable
```

## 8.14 test_assignments

```text
id
test_id
student_id
assigned_at
available_from
available_until
max_attempts
status
```

## 8.15 attempts

```text
id
test_id
student_id
attempt_number
started_at
submitted_at
expires_at
status
score
max_score
percentage
submission_type
```

Statuses:

```text
STARTED
SUBMITTED
AUTO_SUBMITTED
EVALUATED
CANCELLED
```

## 8.16 attempt_answers

```text
id
attempt_id
question_id
selected_option_id nullable
answer_text nullable
numerical_answer nullable
is_marked_for_review
answered_at
```

## 8.17 results

```text
id
attempt_id
student_id
test_id
score
max_score
percentage
correct_count
incorrect_count
unanswered_count
rank nullable
percentile nullable
pass_status
published_at
```

## 8.18 notifications

```text
id
user_id
title
message
type
is_read
created_at
```

## 8.19 audit_logs

```text
id
user_id
module
action
entity_type
entity_id
old_data JSONB nullable
new_data JSONB nullable
ip_address
user_agent
created_at
```

## 8.20 settings

```text
id
setting_key
setting_value
description
is_public
updated_by
updated_at
```

---

# 9. Important Relationships

```text
User
 ├── Roles
 ├── StudentProfile
 └── Notifications

Role
 └── Permissions

Exam
 ├── Subjects
 │    └── Topics
 └── Tests
      ├── TestQuestions
      └── Assignments

Question
 ├── Subject
 ├── Topic
 └── QuestionOptions

Test
 ├── Questions
 ├── Assignments
 └── Attempts

Attempt
 ├── AttemptAnswers
 └── Result
```

---

# 10. Authentication

## Login

```http
POST /api/v1/auth/login
```

Request:

```json
{
  "username": "student@example.com",
  "password": "password"
}
```

Response:

```json
{
  "access_token": "JWT_ACCESS_TOKEN",
  "refresh_token": "JWT_REFRESH_TOKEN",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## Refresh

```http
POST /api/v1/auth/refresh
```

## Current User

```http
GET /api/v1/auth/me
```

## Logout

```http
POST /api/v1/auth/logout
```

JWT should contain minimal identity information, for example:

```json
{
  "sub": "123",
  "type": "access",
  "iat": 1234567890,
  "exp": 1234569690
}
```

Do not put large permission lists into the JWT. Permissions should be resolved server-side or represented through a safe, controlled authorization mechanism.

---

# 11. Authorization / RBAC

Create a reusable dependency:

```python
require_permission("question.create")
```

Example:

```python
@router.post(
    "/",
    dependencies=[Depends(require_permission("question.create"))]
)
async def create_question(...):
    ...
```

Authorization must be enforced on the backend even if the frontend hides unauthorized buttons.

---

# 12. REST API Standard

Base URL:

```text
/api/v1
```

Standard CRUD:

```text
GET    /resources
GET    /resources/{id}
POST   /resources
PUT    /resources/{id}
PATCH  /resources/{id}
DELETE /resources/{id}
```

For actions:

```text
POST /tests/{id}/ready
POST /tests/{id}/publish
POST /tests/{id}/schedule
POST /tests/{id}/activate
POST /tests/{id}/complete
POST /tests/{id}/archive
POST /tests/{id}/close
POST /attempts/{id}/submit
POST /results/{id}/publish
POST /users/{id}/reset-password
```

---

# 13. API Inventory

## Authentication

```text
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
POST /auth/change-password
POST /auth/forgot-password
POST /auth/reset-password
```

## Users

```text
GET    /users
POST   /users
GET    /users/{id}
PUT    /users/{id}
PATCH  /users/{id}/status
DELETE /users/{id}
POST   /users/{id}/reset-password
POST   /users/{id}/roles
GET    /users/{id}/permissions
```

## Roles

```text
GET    /roles
POST   /roles
GET    /roles/{id}
PUT    /roles/{id}
DELETE /roles/{id}
PUT    /roles/{id}/permissions
```

## Permissions

```text
GET /permissions
GET /permissions/modules
```

## Exams

```text
GET    /exams
POST   /exams
GET    /exams/{id}
PUT    /exams/{id}
DELETE /exams/{id}
POST   /exams/{id}/publish
POST   /exams/{id}/archive
```

## Subjects

```text
GET    /subjects
POST   /subjects
GET    /subjects/{id}
PUT    /subjects/{id}
DELETE /subjects/{id}
```

## Topics

```text
GET    /topics
POST   /topics
GET    /topics/{id}
PUT    /topics/{id}
DELETE /topics/{id}
```

## Questions

```text
GET    /questions
POST   /questions
GET    /questions/{id}
PUT    /questions/{id}
DELETE /questions/{id}
POST   /questions/{id}/publish
POST   /questions/import
```

The question listing (`GET /questions`) supports the filters `subject_id`,
`topic_id`, `status`, `question_type`, `difficulty`, `tag` and `is_active`,
plus the shared free-text `search` and pagination/sorting parameters.

## Tests

```text
GET    /tests
POST   /tests
GET    /tests/{id}
PUT    /tests/{id}
DELETE /tests/{id}
POST   /tests/{id}/ready
POST   /tests/{id}/publish
POST   /tests/{id}/schedule
POST   /tests/{id}/activate
POST   /tests/{id}/complete
POST   /tests/{id}/archive
POST   /tests/{id}/close
GET    /tests/{id}/questions
POST   /tests/{id}/questions
POST   /tests/{id}/questions/bulk
DELETE /tests/{id}/questions/{question_id}
GET    /tests/import/template  (download XLSX import template)
POST   /tests/import            (import test + questions from XLSX)
```

Test lifecycle actions move the test through
`DRAFT -> READY -> PUBLISHED -> SCHEDULED/ACTIVE -> COMPLETED -> ARCHIVED`
(see §17). Each action is guarded by the `test.publish` permission and writes
an audit entry.

## Assignments

```text
GET  /assignments
POST /assignments
POST /assignments/bulk
DELETE /assignments/{id}
```

## Student Test APIs

```text
GET  /student/tests
GET  /student/tests/{id}
POST /student/tests/{id}/start
GET  /student/attempts/{attempt_id}
PUT  /student/attempts/{attempt_id}/answers
POST /student/attempts/{attempt_id}/submit
GET  /student/attempts
GET  /student/results
```

## Admin Attempts

```text
GET /attempts
GET /attempts/{id}
GET /attempts/{id}/answers
```

## Results

```text
GET  /results
GET  /results/{id}
POST /results/{id}/publish
GET  /results/export
```

## Reports

```text
GET /reports/dashboard
GET /reports/exams
GET /reports/tests
GET /reports/students/{student_id}
GET /reports/questions
GET /reports/subjects
GET /reports/exams/export
GET /reports/tests/export
GET /reports/students/{student_id}/export
GET /reports/questions/export
GET /reports/subjects/export
```

The JSON endpoints require the `report.view` permission. The `/export`
variants return a UTF-8 CSV attachment with the same columns as the JSON rows
and require the `report.export` permission.

## Notifications

```text
GET   /notifications
PATCH /notifications/{id}/read
POST  /notifications
```

## Audit Logs

```text
GET /audit-logs
GET /audit-logs/{id}
```

## Settings

```text
GET /settings
PUT /settings/{key}
```

---

# 14. Swagger / OpenAPI

FastAPI automatically generates:

```text
Swagger UI:
GET /docs

ReDoc:
GET /redoc

OpenAPI:
GET /openapi.json
```

Every endpoint must include:

- Summary.
- Description.
- Request schema.
- Response schema.
- HTTP status codes.
- Authentication requirement.
- Error responses.
- Query/path parameter descriptions.

Example:

```python
@router.get(
    "/{exam_id}",
    response_model=ExamResponse,
    summary="Get exam",
    description="Return a single exam by numeric ID.",
    responses={
        404: {"description": "Exam not found"},
        403: {"description": "Permission denied"}
    }
)
```

---

# 15. Pagination

All large list endpoints should support:

```text
?page=1&page_size=20
```

Optional:

```text
?search=neet
?status=published
?sort_by=created_at
?sort_order=desc
```

Response:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 100,
  "total_pages": 5
}
```

---

# 16. Standard API Response/Error Model

Success responses may return resource objects directly.

Errors should follow a consistent structure:

```json
{
  "success": false,
  "error": {
    "code": "QUESTION_NOT_FOUND",
    "message": "Question was not found."
  }
}
```

Validation errors should identify the affected field where possible.

Recommended HTTP statuses:

```text
200 OK
201 Created
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
429 Too Many Requests
500 Internal Server Error
```

---

# 17. Test Engine Design

## Test Lifecycle

Tests move through the following statuses. The backend is authoritative for
every transition and rejects invalid ones with `409`; the frontend should hide
actions that are not currently legal.

```text
DRAFT
  |
  v
READY        (POST /tests/{id}/ready)
  |
  v
PUBLISHED    (POST /tests/{id}/publish)
  |
  +--> SCHEDULED  (POST /tests/{id}/schedule)   [scheduled_start_at required]
  |       |
  |       v
  +--> ACTIVE      (POST /tests/{id}/activate)
          |
          v
      COMPLETED   (POST /tests/{id}/complete)
          |
          v
      ARCHIVED    (POST /tests/{id}/archive)
```

`publish` accepts `DRAFT` or `READY`; `close` (`POST /tests/{id}/close`) moves
a `PUBLISHED` test straight to `CLOSED`. A student may start an attempt when the
test status is `PUBLISHED`, `SCHEDULED` (within its window) or `ACTIVE`.

The student test listing only ever exposes `PUBLISHED`, `SCHEDULED`, `ACTIVE`,
`COMPLETED` and `CLOSED` tests; `DRAFT`/`READY` tests are never visible to
students.

## Start Test

When a student starts a test:

1. Validate authentication.
2. Validate student eligibility.
3. Validate test status.
4. Validate availability window.
5. Validate attempt count.
6. Create attempt.
7. Calculate server-side `expires_at`.
8. Return test questions without answer keys.

## Answer Save

Answers should be persisted through:

```text
PUT /student/attempts/{attempt_id}/answers
```

The endpoint must verify that:

- Attempt belongs to authenticated student.
- Attempt is still active.
- Question belongs to the test.
- Current time is before `expires_at`.

## Submit

```text
POST /student/attempts/{attempt_id}/submit
```

The server:

1. Locks/validates the attempt.
2. Prevents duplicate submission.
3. Evaluates answers.
4. Calculates score.
5. Creates result.
6. Marks attempt submitted/evaluated.
7. Returns permitted result data.

---

# 18. Scoring Service

Scoring must be isolated in a dedicated service.

Example:

```python
score = 0

if correct:
    score += positive_marks
elif incorrect:
    score -= negative_marks
```

Support:

- Question-level marks.
- Test-level overrides.
- Negative marking.
- Unanswered questions.
- Multiple correct options.
- Numerical questions.
- Future custom evaluation strategies.

The scoring rules used for an attempt must be reproducible from the test/question configuration applicable at that time.

---

# 19. Database Transactions

Use SQLAlchemy transactions for critical workflows.

Examples:

- Creating a test and its questions.
- Starting an attempt.
- Saving final submission.
- Generating a result.
- Publishing a test.
- Manual result correction.

A failed transaction must not leave partial business data.

---

# 20. Concurrency and Submission Safety

The test submission API must be designed to prevent:

- Double submission.
- Two simultaneous submissions generating two results.
- Submission after expiration.
- Modification of submitted attempts.
- Unauthorized attempt access.

Use database transactions and appropriate row-level locking/atomic state transitions where necessary.

---

# 21. Seed Data

Create:

```text
scripts/seed.py
```

Seed:

### Roles

```text
SUPER_ADMIN
ADMIN
CONTENT_MANAGER
EXAMINER
STUDENT
REPORT_VIEWER
```

### Permissions

Seed all permission codes.

### Users

```text
superadmin@example.com
admin@example.com
teacher@example.com
content@example.com
student@example.com
report@example.com
```

Development passwords must be documented only for local/demo environments.

### Exams

```text
NEET
JEE
UPSC
SSC
CUSTOM
```

### Subjects

Examples:

```text
Physics
Chemistry
Biology
Mathematics
General Studies
English
```

### Sample Questions

Include:

- Single-choice.
- Multiple-choice.
- True/false.
- Numerical.

### Sample Tests

Create at least:

```text
NEET Physics Practice Test
NEET Full Mock Test
JEE Mathematics Practice Test
SSC General Knowledge Test
```

Seed scripts should be idempotent or provide a clear reset option.

---

# 22. Alembic

Initial setup:

```bash
alembic init alembic
```

Generate migration:

```bash
alembic revision --autogenerate -m "initial schema"
```

Run migration:

```bash
alembic upgrade head
```

Rollback:

```bash
alembic downgrade -1
```

Never use `Base.metadata.create_all()` as the production schema-management mechanism.

---

# 23. Security

Required controls:

- HTTPS in production.
- JWT authentication.
- Strong password hashing.
- Backend RBAC.
- Input validation.
- SQL injection protection through SQLAlchemy/parameterized queries.
- XSS-safe output handling.
- CORS restricted to approved frontend origins.
- Rate limiting on authentication/sensitive endpoints.
- Secure token handling.
- No answer-key leakage.
- Ownership checks on student resources.
- Audit logging.
- Environment-based secrets.
- No sensitive information in logs.

---

# 24. Testing Strategy

## Unit Tests

Test:

- Authentication service.
- Permission checks.
- Scoring.
- Eligibility.
- Attempt state transitions.
- Pagination.
- Validation.

## Integration Tests

Test:

- API + PostgreSQL.
- Login.
- CRUD operations.
- Test creation.
- Attempt lifecycle.
- Submission.
- Result generation.

## Security Tests

Test:

- Unauthorized API access.
- Cross-student attempt access.
- Privilege escalation.
- IDOR/BOLA.
- Invalid JWT.
- Expired JWT.
- Answer-key exposure.

## Example

```bash
pytest -v
```

---

# 25. Docker

Recommended services:

```text
backend
postgres
```

No Redis service is required.

Example:

```text
docker-compose.yml
├── api
└── postgres
```

---

# 26. Logging

Use structured application logging.

Log:

- Request ID.
- Endpoint.
- HTTP status.
- Execution time.
- User ID where appropriate.
- Exception information.

Do not log:

- Passwords.
- JWT secrets.
- Refresh tokens.
- Sensitive student information unnecessarily.

---

# 27. Performance

Because no cache is required:

- Use appropriate PostgreSQL indexes.
- Use pagination for large tables.
- Avoid N+1 ORM queries.
- Use `selectinload`/`joinedload` appropriately.
- Use database aggregation for reports.
- Keep transactions short.
- Index foreign keys and frequently filtered columns.

Recommended indexes include:

```text
users.email
users.username
questions.subject_id
questions.topic_id
questions.status
tests.exam_id
tests.status
assignments.test_id
assignments.student_id
attempts.test_id
attempts.student_id
attempt_answers.attempt_id
results.student_id
results.test_id
audit_logs.user_id
audit_logs.created_at
```

---

# 28. Development Commands

Example:

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

alembic upgrade head

python scripts/seed.py

uvicorn app.main:app --reload
```

API:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

---

# 29. Definition of Done — Backend

The backend is considered MVP-ready when:

- PostgreSQL schema is implemented.
- SQLAlchemy models are implemented.
- Alembic migrations work.
- Seed data works.
- Authentication works.
- JWT validation works.
- RBAC works.
- Admin CRUD APIs work.
- Question bank APIs work.
- Test creation/publishing works.
- Student test APIs work.
- Server-side timer is enforced.
- Submission is transaction-safe.
- Scoring works.
- Results work.
- Reports work.
- Swagger documents all APIs.
- API tests cover critical workflows.
- Security checks are completed.
- Test import from XLSX validates against exam, auto-creates subjects/topics when missing (per spec), keeps imported test/questions in `DRAFT`, returns per-row validation errors on failure and writes audit entry.
- No cache dependency exists.

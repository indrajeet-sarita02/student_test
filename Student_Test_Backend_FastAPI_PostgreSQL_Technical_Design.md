# Student Test Application — Backend Technical Design & Development Specification

## Removal notice (test-taking subsystem)

> **The test-assembly / test-taking / scoring / results / reports subsystem has
> been removed from the backend.** The following are no longer part of the
> application:
>
> - **Models & tables:** `tests`, `test_questions`, `test_assignments`,
>   `attempts`, `attempt_answers`, `results`.
> - **API modules & endpoints:** `/tests`, `/assignments`, `/attempts`,
>   `/results`, `/reports` and `/student` (including the XLSX test-import
>   endpoint and its template download).
> - **Services & repositories:** test assembly, assignment, attempt, scoring,
>   test-import and report services plus their repositories and schemas.
> - **Permissions & roles:** `test.*`, `attempt.*`, `result.*`, `report.view`
>   and the `TEST_ASSIGNED` / `RESULT_PUBLISHED` notification types (and the
>   `TestStatus` / `AssignmentStatus` / `AttemptStatus` / `SubmissionType`
>   enums).
> - **Migration:** `c4d8e2f6a1b3_drop_test_domain_tables` drops the tables
>   listed above.
>
> What remains is the **content & administration core**: JWT authentication,
> RBAC, users/roles/permissions, exams, subjects, topics, the question bank,
> notifications, audit logs and settings.
>
> Sections below that describe the removed subsystem (notably **8.12–8.17**,
> the test/admin-attempt/result/report parts of **13**, **17**, **18**, **20**,
> the test parts of **21**, and **24**) are retained for historical context only
> and **no longer describe the running system**. Treat them as archival.

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
| Testing | Not included (the test subsystem and its pytest suite were removed) |
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
- Historical audit-log entries must remain consistent and immutable.

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
   | Auth / RBAC |      |  Services   |      |   Content   |
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
│   │   └── common.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── exam_repository.py
│   │   └── question_repository.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── exam_service.py
│   │   ├── question_service.py
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

Prefer soft deletion (or `is_active` flags) for content such as exams, subjects, topics and questions.

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
notification.view
notification.create
audit.view
settings.view
settings.update
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
created_by
updated_by
created_at
updated_at
```

## 8.11 question_options

```text
id
question_id
option_text
option_order
is_correct
```

For security, `is_correct` should never be exposed through any public/read-only API.

## 8.12–8.17 Tests, assignments, attempts & results — REMOVED

> **Removed.** The `tests`, `test_questions`, `test_assignments`, `attempts`,
> `attempt_answers` and `results` tables (and their models, schemas,
> repositories, services and endpoints) have been dropped from the application.
> Migration `c4d8e2f6a1b3_drop_test_domain_tables` removes them. The historical
> column definitions were: `tests` (exam_id, name, code, description,
> instructions, duration_minutes, total_marks, passing_marks,
> negative_marking_enabled, negative_marks, randomize_questions,
> randomize_options, max_attempts, status, scheduled_start_at, scheduled_end_at,
> audit columns); `test_questions` (test_id, question_id, question_order,
> marks_override, negative_marks_override); `test_assignments` (test_id,
> student_id, assigned_at, available_from, available_until, max_attempts,
> status); `attempts` (test_id, student_id, attempt_number, started_at,
> submitted_at, expires_at, status, score, max_score, percentage,
> submission_type); `attempt_answers` (attempt_id, question_id,
> selected_option_id, answer_text, numerical_answer, is_marked_for_review,
> answered_at); `results` (attempt_id, student_id, test_id, score, max_score,
> percentage, correct_count, incorrect_count, unanswered_count, rank, percentile,
> pass_status, published_at).
>
> The numbering gap is intentional so the surviving sections keep their numbers.

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
 └── Subjects
      └── Topics

Question
 ├── Subject
 ├── Topic
 └── QuestionOptions
```

> **Removed.** `Tests`, `TestQuestions`, `Assignments`, `Attempts`,
> `AttemptAnswers` and `Results` and their relationships have been dropped.

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
POST /exams/{id}/publish
POST /exams/{id}/archive
POST /questions/{id}/publish
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

## Tests, Assignments, Attempts, Results & Reports — REMOVED

> **Removed.** The `/tests`, `/assignments`, `/attempts`, `/results`, `/reports`
> and `/student` routers (and every endpoint they exposed, including the XLSX
> test-import and template download) have been deleted from the API. They were:
>
> ```text
> # tests
> GET/POST /tests, GET/PUT/DELETE /tests/{id}, POST /tests/{id}/publish,
> POST /tests/{id}/close, POST/DELETE /tests/{id}/questions..., 
> GET /tests/import/template, POST /tests/import
> # assignments
> GET/POST /assignments, POST /assignments/bulk, DELETE /assignments/{id}
> # student
> GET /student/tests, GET /student/tests/{id}, POST /student/tests/{id}/start,
> GET/PUT/POST /student/attempts/{id}..., GET /student/attempts,
> GET /student/results
> # admin attempts / results / reports
> GET /attempts..., GET /results..., GET /reports/...
> ```
>
> Only the content & administration endpoints below remain.

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

# 17. Test Engine Design — REMOVED

> **Removed.** The server-timed test engine (attempt start, answer autosave and
> submission endpoints under `/student/...`) has been deleted along with the
> `attempts` / `attempt_answers` tables and the student router. There is no
> test-taking flow in the current application.

---

# 18. Scoring Service — REMOVED

> **Removed.** The scoring service (`app/services/scoring_service.py`) that
> evaluated answers, applied positive/negative marking and produced results has
> been deleted together with the `results` table and its endpoints.

---

# 19. Database Transactions

Use SQLAlchemy transactions for critical workflows.

Examples:

- Creating an exam with its subjects and topics.
- Importing questions in bulk.
- Publishing an exam or question.
- Assigning roles to a user.
- Recording audit-log entries.

A failed transaction must not leave partial business data.

---

# 20. Concurrency and Submission Safety — REMOVED

> **Removed.** Submission-safety concerns (double submission, expiry races,
> `SELECT ... FOR UPDATE` on attempts) applied only to the deleted test-taking
> flow and no longer apply.

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

### Sample Tests — REMOVED

> **Removed.** Tests are no longer seeded (the `tests` / `test_questions` /
> `test_assignments` tables were dropped). The seeder now covers permissions,
> roles, users, student profiles, exams, subjects, topics, questions, question
> options and settings only.

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
- No leakage of question answer keys through any read-only API.
- Audit logging.
- Environment-based secrets.
- No sensitive information in logs.

---

# 24. Testing Strategy — REMOVED

> **Removed.** The pytest suite (`backend/tests/`, `pytest.ini`, the `pytest`
> dependency and the `httpx`-based TestClient harness) has been deleted. There
> is currently no automated backend test suite; the application is verified by
> `python -c "import app.main"`, `alembic check` and manual/smoke checks.
>
> If automated tests are reintroduced, cover the surviving core: authentication,
> permission checks, CRUD for exams/subjects/topics/questions, pagination,
> validation and audit logging.

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
- Keep transactions short.
- Index foreign keys and frequently filtered columns.

Recommended indexes include:

```text
users.email
users.username
questions.subject_id
questions.topic_id
questions.status
subjects.exam_id
topics.subject_id
notifications.user_id
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
- Subject/topic and exam management work.
- Notification, audit-log and settings APIs work.
- Swagger documents all APIs.
- Security checks are completed.

> **Note.** The former definition-of-done items for test creation/publishing,
> the student test APIs, the server-side timer, transaction-safe submission,
> scoring, results, reports and XLSX test import no longer apply — that
> subsystem has been removed.
- No cache dependency exists.

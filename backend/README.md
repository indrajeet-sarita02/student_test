# Student Test Application — Backend

FastAPI + SQLAlchemy 2.x + PostgreSQL REST API for a student examination /
test platform. Implements the specification in
[`../Student_Test_Backend_FastAPI_PostgreSQL_Technical_Design.md`](../Student_Test_Backend_FastAPI_PostgreSQL_Technical_Design.md):
JWT authentication, role-based access control, exam & question-bank management,
test assembly and assignment, a server-timed test engine with transaction-safe
submission, scoring with negative marking, results, reports and audit logging.

## Stack

| Concern | Choice |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x (typed declarative) |
| Database | PostgreSQL (Prisma Postgres or any Postgres 14+) |
| Migrations | Alembic |
| Validation | Pydantic v2 + pydantic-settings |
| Auth | JWT (PyJWT), access + refresh tokens |
| Passwords | Argon2id (`pwdlib`) |
| Tests | Pytest + HTTPX / Starlette TestClient |

## Quick start (local)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # or: uv venv --python 3.12 .venv
pip install -r requirements.txt

cp .env.example .env        # then edit DATABASE_URL / JWT_SECRET_KEY

alembic upgrade head        # create the schema
python scripts/seed.py      # idempotent demo data (--reset to wipe first)
uvicorn app.main:app --reload
```

- API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI JSON: <http://localhost:8000/openapi.json>
- Health: <http://localhost:8000/health>

### Environment variables (`.env`)

```env
APP_NAME=Student Test API
APP_ENV=development
DEBUG=true
DATABASE_URL=postgres://user:pass@host:5432/postgres?sslmode=require
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:3000
PASSWORD_HASH_ALGORITHM=argon2
```

`postgres://` and `postgresql://` URLs are normalised to the `psycopg` driver
automatically (`app/core/config.py`), so the Prisma Postgres URL can be pasted
as-is.

## Demo accounts (seeded, dev-only)

All seeded accounts share the password **`Admin@123`**:

| Email | Role |
|---|---|
| `superadmin@example.com` | SUPER_ADMIN |
| `admin@example.com` | ADMIN |
| `teacher@example.com` | EXAMINER |
| `content@example.com` | CONTENT_MANAGER |
| `report@example.com` | REPORT_VIEWER |
| `student@example.com` | STUDENT |
| `student2@example.com` | STUDENT |

> These credentials exist only for local/demo environments. Never ship them to
> production.

## API layout

All routes are served under `/api/v1`.

| Module | Prefix | Highlights |
|---|---|---|
| Authentication | `/auth` | login, refresh, logout, me, change/forgot/reset password |
| Users | `/users` | CRUD, status, role assignment, permissions |
| Roles / Permissions | `/roles`, `/permissions` | RBAC administration |
| Exams | `/exams` | CRUD, publish, archive |
| Subjects / Topics | `/subjects`, `/topics` | syllabus tree |
| Questions | `/questions` | CRUD, publish, bulk import |
| Tests | `/tests` | assembly, publish/close, add/remove questions |
| Assignments | `/assignments` | assign tests to students (single/bulk) |
| Admin attempts | `/attempts` | attempt + answer inspection |
| Results | `/results` | list, publish, CSV export |
| Reports | `/reports` | dashboard, exam/test/student/question/subject analytics |
| Student tests | `/student` | list/start/answer/submit/review, own results |
| Notifications | `/notifications` | inbox, mark read, admin create |
| Audit logs | `/audit-logs` | administrative audit trail |
| Settings | `/settings` | public + private key/value settings |

Successful responses return resource objects directly (or a pagination
envelope `{items, page, page_size, total, total_pages}`). Errors always use:

```json
{ "success": false, "error": { "code": "QUESTION_NOT_FOUND", "message": "Question was not found." } }
```

## Test engine & security notes

- Test duration is enforced **server-side**: an attempt gets an `expires_at` at
  start; saving answers after expiry triggers auto-submission.
- Submissions take a row lock (`SELECT ... FOR UPDATE`) and transition the
  attempt state atomically, so double/concurrent submissions cannot create two
  results.
- Answer keys (`is_correct`, explanations, correct option ids) are never
  returned by test-taking endpoints; they are available only after submission
  via `/student/results/{id}/review`.
- Authorization is always enforced server-side using the RBAC permission
  catalogue; ownership checks return `404` (not `403`) to avoid IDOR leaks.
- Login failures are rate-limited (sliding window) per identifier+IP.

## Migrations

```bash
alembic upgrade head            # apply
alembic downgrade -1            # rollback one revision
alembic revision --autogenerate -m "message"
alembic check                   # detect model/migration drift
```

## Tests

```bash
pytest -v
```

Integration tests run against a **separate, per-run PostgreSQL schema**
(`student_test_pytest_<pid>`) created and dropped automatically, so your real
data is never touched and two concurrent runs cannot collide. If that schema
cannot be created (e.g. restricted credentials), the DB-backed tests are
skipped and the unit tests still run.

## Docker

```bash
docker compose up --build              # API against the DATABASE_URL from .env
docker compose --profile local-db up   # also start a local PostgreSQL
```

## Project structure

```text
app/
  main.py            FastAPI app, error handlers, health, CORS
  core/              config, security, JWT, RBAC, exceptions
  db/                declarative base + mixins, engine/session
  models/            SQLAlchemy models (21 tables)
  schemas/           Pydantic request/response models
  repositories/      reusable query layer
  services/          business logic + transactions
  api/v1/            routers per module
  utils/             pagination, enums, datetime helpers
alembic/             migrations
scripts/seed.py      idempotent demo data
tests/               unit + integration tests
```

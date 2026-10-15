# Student Test Application — Backend

FastAPI + SQLAlchemy 2.x + PostgreSQL REST API for a student examination
content platform. Implements the specification in
[`../Student_Test_Backend_FastAPI_PostgreSQL_Technical_Design.md`](../Student_Test_Backend_FastAPI_PostgreSQL_Technical_Design.md):
JWT authentication, role-based access control, exam / subject / topic and
question-bank management, notifications, settings and audit logging.

> **Removed.** The test-assembly, test-assignment, test-taking (attempts),
> scoring, results and reports subsystem — and its pytest suite — have been
> removed. The related tables (`tests`, `test_questions`, `test_assignments`,
> `attempts`, `attempt_answers`, `results`) are dropped by the
> `c4d8e2f6a1b3_drop_test_domain_tables` migration. The test-domain API modules
> (`/tests`, `/assignments`, `/attempts`, `/results`, `/reports`, `/student`)
> and their permissions (`test.*`, `attempt.view`, `result.*`, `report.view`)
> no longer exist.

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
| Notifications | `/notifications` | inbox, mark read, admin create |
| Audit logs | `/audit-logs` | administrative audit trail |
| Settings | `/settings` | public + private key/value settings |

Successful responses return resource objects directly (or a pagination
envelope `{items, page, page_size, total, total_pages}`). Errors always use:

```json
{ "success": false, "error": { "code": "QUESTION_NOT_FOUND", "message": "Question was not found." } }
```

## Security notes

- Authorization is always enforced server-side using the RBAC permission
  catalogue; ownership checks return `404` (not `403`) to avoid IDOR leaks.
- Question answer keys (`is_correct`, correct option ids) are not exposed
  through list/get responses beyond what the question CRUD endpoints require.
- Login failures are rate-limited (sliding window) per identifier+IP.

## Migrations

```bash
alembic upgrade head            # apply
alembic downgrade -1            # rollback one revision
alembic revision --autogenerate -m "message"
alembic check                   # detect model/migration drift
```

## Verification

There is no automated test suite. Verify the app imports and the schema is in
sync instead:

```bash
python -c "import app.main"   # import check
alembic check                 # model/migration drift check
```

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
  models/            SQLAlchemy models (15 tables)
  schemas/           Pydantic request/response models
  repositories/      reusable query layer
  services/          business logic + transactions
  api/v1/            routers per module
  utils/             pagination, enums, datetime helpers
alembic/             migrations
scripts/seed.py      idempotent demo data
```

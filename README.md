# Student Test Platform

A full-stack MCQ examination platform: a **FastAPI + PostgreSQL** backend and a
**Next.js (App Router)** frontend for managing exams, subjects, topics, the
question bank, users/RBAC, test assembly and assignment, server-timed test
taking, scoring, results, reports, notifications, audit logs and settings.

## Repository layout

| Path | Description |
|---|---|
| [`backend/`](backend/) | FastAPI + SQLAlchemy 2.x + PostgreSQL REST API — see [`backend/README.md`](backend/README.md) |
| [`frontend/`](frontend/) | Next.js + React + TypeScript + Tailwind client |
| [`Student_Test_Backend_FastAPI_PostgreSQL_Technical_Design.md`](Student_Test_Backend_FastAPI_PostgreSQL_Technical_Design.md) | Backend technical design |
| [`Student_Test_Frontend_NextJS_Technical_Design.md`](Student_Test_Frontend_NextJS_Technical_Design.md) | Frontend technical design |

## Architecture

```text
Browser
  │  same-origin fetch  (/api/backend/*, no CORS)
  ▼
Next.js  ── proxy route handler ──►  FastAPI  ──►  PostgreSQL
(port 3000)                          (port 8000)
```

- The browser only talks to the Next.js origin. The catch-all route handler at
  `frontend/src/app/api/backend/[...path]/route.ts` proxies requests to the
  backend's `/api/v1/*`, preserving path, method, headers and body.
- Auth is JWT-based (access + refresh). The backend is authoritative for RBAC;
  the frontend hides UI and guards routes to match.

## Prerequisites

- **Python** 3.12 (backend)
- **Node.js** >= 16.14 (frontend)
- A **PostgreSQL** 14+ database (any Postgres, incl. Prisma Postgres)

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # or: uv venv --python 3.12 .venv
pip install -r requirements.txt

cp .env.example .env        # then edit DATABASE_URL / JWT_SECRET_KEY
alembic upgrade head        # create the schema
python scripts/seed.py      # idempotent demo data (--reset to wipe first)
uvicorn app.main:app --reload
```

- API: <http://localhost:8000> · Swagger: `/docs` · Health: `/health`
- Run tests with `pytest -v` (see [`backend/README.md`](backend/README.md) for
  the full API layout, migrations, Docker usage and project structure).

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # edit BACKEND_URL if the API runs elsewhere
npm run dev
```

- App: <http://localhost:3000>

Frontend scripts: `npm run dev` · `npm run build` · `npm run start` ·
`npm run lint`.

#### Frontend structure

```text
src/
  app/
    api/backend/[...path]/route.ts   same-origin proxy to FastAPI
    (main)/                          student-facing pages (tests, results,
                                     history, notifications, profile)
    attempts/[attemptId]/            live test-taking screen
    admin/                           admin console (exams, subjects, topics,
                                     questions, tests, assignments, attempts,
                                     results, reports, users, roles,
                                     permissions, notifications, audit-logs,
                                     settings, upload, profile)
    login/ forgot-password/ reset-password/
  components/                        DataTable, Modal, Toast, guards, layout,
                                     admin + student widgets
  lib/                               api client, auth, permissions, types,
                                     hooks, test-import helpers
```

Role-based guards (`src/components/guards.tsx` + `src/lib/permissions.ts`) hide
UI the current user cannot use; the backend still enforces every permission.

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

## Key environment variables

| App | Variable | Purpose |
|---|---|---|
| backend | `DATABASE_URL` | PostgreSQL connection string (`postgres://` / `postgresql://` are normalised to `psycopg`) |
| backend | `JWT_SECRET_KEY` | Token signing secret |
| backend | `CORS_ORIGINS` | Allowed browser origins when calling the API directly |
| frontend | `BACKEND_URL` | Server-side proxy target (defaults to `http://127.0.0.1:8000` locally, deployed backend on Vercel) |
| frontend | `NEXT_PUBLIC_API_BASE_URL` | Optional direct-call base URL; leave unset to use the same-origin proxy |

## Deployment

- **Backend:** container image (`backend/Dockerfile`) or any Python host;
  `docker compose up` runs it against the configured database.
- **Frontend:** Vercel — the proxy defaults to the deployed backend, so no extra
  configuration is required (override with `BACKEND_URL`).

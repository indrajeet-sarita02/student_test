# Student Test Application — Frontend

Next.js (App Router) + React 18 + TypeScript + Tailwind CSS client for the
Student Test platform. It implements the specification in
[`../Student_Test_Frontend_NextJS_Technical_Design.md`](../Student_Test_Frontend_NextJS_Technical_Design.md):
authentication, the student portal, and the admin console for users,
roles/permissions, exams, the subject → topic → question bank, notifications,
audit logs and settings.

> **Removed.** The test-taking UI (test lists, test runner, attempts, results,
> reports and assignments pages) has been removed along with the backend
> test-domain subsystem. The remaining pages are the ones listed under
> [Routes](#routes).

## Stack

| Concern | Choice |
|---|---|
| Framework | Next.js 13.5 (App Router) |
| UI | React 18 + TypeScript 5 |
| Styling | Tailwind CSS 3 (custom `brand` palette) |
| Data fetching | tiny in-house `useApi` hook + typed `api` client |
| Auth | JWT bearer tokens, one-shot refresh, RBAC-driven UI |
| BFF | same-origin Next route handler proxying the FastAPI backend |

## Quick start (local)

```bash
cd frontend
npm install
cp .env.example .env.local     # then edit BACKEND_URL if needed
npm run dev
```

- App: <http://localhost:3000>
- Health (proxied): <http://localhost:3000/api/health>

The backend must be running (default target `http://127.0.0.1:8000`). See the
[`../backend/README.md`](../backend/README.md) to start it.

Node **>= 16.14.0** is required (Next 13.5).

## Environment variables (`.env.local`)

| Variable | Scope | Purpose |
|---|---|---|
| `BACKEND_URL` | server only | Target origin for the `/api/backend/*` proxy and the `/api/health` rewrite. Defaults to `http://127.0.0.1:8000` locally and to the deployed backend (`https://student-testapi.vercel.app`) on Vercel. |
| `NEXT_PUBLIC_API_BASE_URL` | browser | Optional. When set, the browser calls the backend **directly** at e.g. `http://localhost:8000/api/v1` (the backend must allow this origin in `CORS_ORIGINS`). When unset (recommended), requests go through the same-origin `/api/backend` proxy and no CORS is needed. |

## How the frontend talks to the API

The browser only ever calls the **same origin**:

1. `src/app/api/backend/[...path]/route.ts` proxies `/api/backend/<path>` to
   `${BACKEND_URL}/api/v1/<path>`, preserving the exact path (including trailing
   slashes), method, headers and body. This avoids CORS and stops FastAPI
   redirects from pointing the browser at an absolute backend URL (which would
   drop the `Authorization` header).
2. `next.config.js` sets `skipTrailingSlashRedirect: true` for the same reason,
   uses worker threads for the catch-all route, and rewrites `/api/health` →
   `${BACKEND_URL}/health` and `/favicon.ico` → `/icon.svg`.
3. The proxy retries transient upstream failures and, when a request carries no
   `Authorization` header, rebuilds one from the first-party `st_access_token`
   cookie (set at login) so direct navigations stay authenticated.

Token handling lives in `src/lib/api/client.ts`:

- access + refresh tokens in `localStorage` (`st_access_token`,
  `st_refresh_token`); the access token is mirrored to a cookie for the proxy.
- a `401` triggers a single shared refresh and replays the request; a network
  error never clears a valid session.
- errors are normalised to `ApiError { code, message, details }`.

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start the dev server on port 3000 |
| `npm run build` | Production build |
| `npm run start` | Serve the production build on port 3000 |
| `npm run lint` | Next.js lint |

## Routes

| Area | Path | Notes |
|---|---|---|
| Public | `/login` | Username **or** email; redirects to `/admin` for staff, `/` otherwise |
| Public | `/forgot-password`, `/reset-password` | Token-based password reset |
| Student | `/` | Dashboard (welcome, notification summary) |
| Student | `/notifications`, `/profile` | Inbox + own profile |
| Admin | `/admin` | Console dashboard (requires a staff role) |
| Admin | `/admin/users`, `/admin/roles`, `/admin/permissions` | RBAC administration |
| Admin | `/admin/exams`, `/admin/subjects`, `/admin/topics`, `/admin/questions` | Content management |
| Admin | `/admin/notifications`, `/admin/audit-logs`, `/admin/settings` | Operations |
| Admin | `/admin/profile` | Own profile |

Route groups: `src/app/(main)/*` is the authenticated student shell; `src/app/admin/*`
is the admin shell. Both wrap pages in `RequireAuth` (`staffOnly` for admin).

## RBAC

The backend is authoritative; the frontend only hides UI and guards routes
(`src/lib/permissions.ts`):

- `SUPER_ADMIN` is represented by the `"*"` permission.
- `ADMIN_ROLES` = `SUPER_ADMIN`, `ADMIN`, `CONTENT_MANAGER`, `EXAMINER`,
  `REPORT_VIEWER`; these users land on `/admin`.
- `hasPermission` / `hasAnyPermission` drive nav filtering
  (`src/lib/navigation.ts`) and button visibility.

## Project structure

```text
src/
  app/
    layout.tsx                 Root layout + providers
    providers.tsx              Toast + Auth providers
    login, forgot-password, reset-password/
    (main)/                    Authenticated student shell + pages
    admin/                     Admin shell + pages
    api/backend/[...path]/     Same-origin FastAPI proxy route handler
  components/                  UI kit, AppShell, guards, DataTable, CRUD manager…
  lib/
    api/client.ts              fetch wrapper, token store, refresh, errors
    api/endpoints.ts           one typed function per backend endpoint
    auth/auth-context.tsx      session state + login/logout/refresh
    permissions.ts             RBAC helpers
    navigation.ts              sidebar definitions (filtered by permission)
    hooks.ts, utils.ts, options.ts, types.ts
```

## Deployment

On Vercel the proxy defaults to the deployed backend, so no configuration is
needed. Set `BACKEND_URL` to point at a different backend, or
`NEXT_PUBLIC_API_BASE_URL` to bypass the proxy and call the backend directly
(CORS required). `eslint` is ignored during builds (`next.config.js`).

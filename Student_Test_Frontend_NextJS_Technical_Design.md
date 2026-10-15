# Student Test Application — Frontend Technical Design & Development Specification

## Removal notice (test-taking subsystem)

> **The student test-taking UI and every admin screen that managed tests has
> been removed from the frontend**, alongside the deleted backend subsystem.
> The following are no longer part of the application:
>
> - **Admin routes:** `/admin/tests`, `/admin/upload`, `/admin/assignments`,
>   `/admin/attempts`, `/admin/results`, `/admin/reports`.
> - **Student routes:** `/tests`, `/tests/[id]`, `/history`, `/results`,
>   `/results/[id]` and `/attempts/[attemptId]` (the test player).
> - **API modules (`src/lib/api/endpoints.ts`):** `testsApi`, `assignmentsApi`,
>   `attemptsApi`, `resultsApi`, `reportsApi`, `studentApi`.
> - **Types (`src/lib/types.ts`):** test / assignment / attempt / student /
>   result / report types (`TestResponse`, `AssignmentResponse`,
>   `AttemptResponse`, `ResultResponse`, `DashboardReport`, …).
> - **Navigation:** the admin *Reports / Tests / Upload XLSX / Assignments /
>   Attempts / Results* items and the student *Available Tests / My Attempts /
>   My Results* items.
> - **Components / helpers:** `components/student/StartTestButton.tsx`,
>   `lib/test-import.ts` and the option loaders that referenced tests.
> - **Permissions:** `test.*`, `attempt.view`, `result.*`, `report.view`.
>
> What remains is the **content & administration core**: login/auth, role-based
> dashboards, users, roles & permissions, exams, subjects, topics, the question
> bank, notifications, audit logs, settings and the student profile.
>
> Sections below that describe the removed subsystem (notably **19–29**, the
> test-related parts of **11/12/36/45/47/48** and **51**) are retained for
> historical context only and **no longer describe the running UI**.

## 1. Document Overview

| Item | Specification |
|---|---|
| Frontend Framework | Next.js |
| Language | TypeScript |
| Rendering | Next.js App Router recommended |
| UI | Responsive Web Application |
| Backend | FastAPI REST API |
| API Communication | HTTPS/JSON |
| Authentication | JWT through backend |
| Authorization | Backend-driven RBAC + frontend route/UI guards |
| State | React state + server/API state |
| Cache | No application cache |
| API Documentation | Backend Swagger |
| Form Validation | Zod or equivalent |
| Testing | Not included (the test domain and its test suite were removed) |

---

# 2. Frontend Objective

The Next.js application will provide:

- Public authentication screens.
- Role-based dashboards.
- Administrative management interfaces.
- Exam / subject / topic management.
- Question-bank management.
- Notifications, audit logs and settings.
- Responsive UI.
- Secure integration with FastAPI.

The frontend is not the final security boundary. All permissions must also be validated by FastAPI.

---

# 3. Recommended Frontend Structure

```text
frontend/
├── src/
│   ├── app/
│   │   ├── (public)/
│   │   │   ├── login/
│   │   │   ├── forgot-password/
│   │   │   └── reset-password/
│   │   │
│   │   ├── (dashboard)/
│   │   │   ├── dashboard/
│   │   │   ├── users/
│   │   │   ├── roles/
│   │   │   ├── permissions/
│   │   │   ├── exams/
│   │   │   ├── subjects/
│   │   │   ├── topics/
│   │   │   ├── questions/
│   │   │   ├── notifications/
│   │   │   ├── audit-logs/
│   │   │   ├── settings/
│   │   │   └── profile/
│   │   │
│   │   └── layout.tsx
│   │
│   ├── components/
│   │   ├── ui/
│   │   ├── forms/
│   │   ├── tables/
│   │   └── modals/
│   │
│   ├── lib/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── permissions/
│   │   ├── validators/
│   │   └── utils/
│   │
│   ├── hooks/
│   ├── types/
│   ├── constants/
│   └── middleware.ts
│
├── public/
├── .env.example
├── package.json
└── README.md
```

---

# 4. Frontend Architecture

```text
Next.js
   |
   +-- App Router
   |
   +-- Route Protection
   |
   +-- Layouts
   |
   +-- Components
   |
   +-- API Client
   |
   +-- Auth / Permission Layer
   |
   +-- FastAPI
```

Recommended separation:

```text
UI Components
     ↓
Feature Hooks
     ↓
API Client
     ↓
FastAPI REST API
```

Avoid putting direct fetch calls throughout arbitrary UI components.

---

# 5. Environment Configuration

`.env.example`

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

Production:

```env
NEXT_PUBLIC_API_BASE_URL=https://api.example.com/api/v1
```

Do not place backend secrets in Next.js `NEXT_PUBLIC_*` variables.

---

# 6. API Client

Create:

```text
src/lib/api/client.ts
```

Responsibilities:

- Base URL.
- Authorization.
- JSON handling.
- Error normalization.
- Request timeout.
- Common headers.
- Refresh-token handling if selected.

Example interface:

```ts
api.get<T>(url)
api.post<T>(url, body)
api.put<T>(url, body)
api.patch<T>(url, body)
api.delete<T>(url)
```

---

# 7. Authentication

Frontend screens:

```text
/login
/forgot-password
/reset-password
```

After login:

```text
access token
refresh token
user profile
roles
permissions
```

Recommended approach:

- Prefer secure HttpOnly cookies when architecture permits.
- Do not expose refresh tokens to JavaScript unnecessarily.
- Never store passwords in browser storage.
- Do not use `localStorage` for long-lived sensitive tokens if secure HttpOnly cookie architecture is available.

The exact token transport must be aligned with FastAPI authentication implementation.

---

# 8. Authentication Flow

```text
Login Page
    |
    v
POST /auth/login
    |
    v
FastAPI validates credentials
    |
    v
JWT/session returned
    |
    v
GET /auth/me
    |
    v
Load roles + permissions
    |
    v
Redirect to dashboard
```

On `401`:

```text
Try refresh
   |
   +-- success --> retry request
   |
   +-- failure --> logout and redirect /login
```

---

# 9. Role-Based Frontend Access

Roles:

```text
SUPER_ADMIN
ADMIN
CONTENT_MANAGER
EXAMINER
STUDENT
REPORT_VIEWER
```

Permission helper:

```ts
hasPermission("question.create")
```

Component example:

```tsx
{hasPermission("question.create") && (
  <CreateQuestionButton />
)}
```

Route protection must be implemented in addition to UI hiding.

---

# 10. Application Layout

Authenticated layout:

```text
+---------------------------------------------------+
| Header                              Profile       |
+----------------+----------------------------------+
| Sidebar        | Main Content                     |
|                |                                  |
| Dashboard      | Page                             |
| Exams          |                                  |
| Subjects       |                                  |
| Topics         |                                  |
| Questions      |                                  |
| Users          |                                  |
| Roles          |                                  |
| Notifications  |                                  |
| Audit Logs     |                                  |
| Settings       |                                  |
+----------------+----------------------------------+
```

Sidebar items should be dynamically filtered by permissions.

---

# 11. Admin Dashboard

Display:

- Total users.
- Total exams.
- Total questions.
- Quick links to users, exams and the question bank.

The dashboard no longer calls a reports API. It derives its counters from the
resource list endpoints (requesting a single item per resource and reading the
pagination `total`):

```text
GET /users?page=1&page_size=1
GET /exams?page=1&page_size=1
GET /questions?page=1&page_size=1
```

> The former `GET /reports/dashboard` and the test/attempt/result statistics
> have been removed.

---

# 12. Student Dashboard

Display:

- Welcome message.
- Recent notifications.
- A link to the profile screen.

APIs:

```text
GET /notifications
GET /notifications/unread-count
```

> The former student dashboard (available tests, in-progress tests, recent
> results, subject performance) relied on `/student/*` endpoints that have been
> removed.

---

# 13. User Management UI

Routes:

```text
/users
/users/create
/users/[id]
/users/[id]/edit
```

Features:

- Search.
- Filter.
- Pagination.
- Create user.
- Edit user.
- Activate/deactivate.
- Assign roles.
- View permissions.
- Reset password where authorized.

---

# 14. Role Management UI

Routes:

```text
/roles
/roles/create
/roles/[id]/edit
```

Features:

- Create role.
- Edit role.
- Assign permissions.
- Remove permissions.
- View permission matrix.

Example matrix:

| Module | View | Create | Update | Delete | Publish |
|---|---:|---:|---:|---:|---:|
| Users | ✓ | ✓ | ✓ | ✓ | - |
| Exams | ✓ | ✓ | ✓ | ✓ | ✓ |
| Questions | ✓ | ✓ | ✓ | ✓ | ✓ |
| Tests | ✓ | ✓ | ✓ | ✓ | ✓ |
| Results | ✓ | - | - | - | ✓ |

---

# 15. Exam Management

Routes:

```text
/exams
/exams/create
/exams/[id]
/exams/[id]/edit
```

Fields:

```text
name
code
description
exam_type
duration
passing_percentage
start_at
end_at
status
```

Actions:

```text
Create
Edit
Publish
Archive
View Subjects
View Tests
```

---

# 16. Subject & Topic Management

Exam:

```text
Exam
  └── Subject
       └── Topic
            └── Subtopic
```

The UI should support:

- Add subject.
- Edit subject.
- Reorder subject.
- Add topic.
- Edit topic.
- Parent topic where supported.
- Activate/deactivate.

---

# 17. Question Bank

Routes:

```text
/questions
/questions/create
/questions/[id]
/questions/[id]/edit
```

Filters:

```text
Exam
Subject
Topic
Question Type
Difficulty
Status
Tag
```

Question editor supports:

```text
Question Text
Options
Correct Answer
Explanation
Marks
Negative Marks
Difficulty
Subject
Topic
Tags
Source
```

Important:

The student frontend must never receive the `is_correct` field before submission.

---

# 18. Question Types

Initial support:

```text
SINGLE_CHOICE
MULTIPLE_CHOICE
TRUE_FALSE
NUMERICAL
```

The component system should allow future:

```text
MATCHING
ASSERTION_REASON
COMPREHENSION
IMAGE_BASED
```

without redesigning the question renderer.

---

# 19–29. Test-taking UI — REMOVED

> **Removed.** The entire student test-taking experience and its administration
> screens were deleted together with the backend test subsystem. The following
> sections are retained only as historical design context and no longer
> describe the running UI:
>
> - **19. Test Builder** and **20. Test Publishing Workflow** → the
>   `/admin/tests` page (assembly, publish/close, XLSX import) was removed.
> - **21. Assignment Management** → `/admin/assignments` was removed.
> - **22. Student Test Player**, **23. Timer Requirements**, **24. Autosave**
>   and **25. Submission** → `/tests/[id]` and `/attempts/[attemptId]` were
>   removed.
> - **26. Result Screen** and **27. Student History** → `/results`,
>   `/results/[id]` and `/history` were removed.
> - **28. Reports** and **29. Export** → `/admin/reports` and the CSV/XLSX
>   export actions were removed.
>
> The remaining student surface is the home dashboard (welcome message +
> recent notifications), the notification inbox and the profile screen. The
> remaining admin surface is the dashboard plus users, roles, permissions,
> exams, subjects, topics, questions, notifications, audit logs, settings and
> profile.

# 30. Notifications

Notification UI:

```text
Header Bell
    |
    +-- Test Published
    +-- Test Starting Soon
    +-- Result Published
    +-- Admin Message
```

API:

```text
GET /notifications
PATCH /notifications/{id}/read
```

---

# 31. Forms

Use schema-based validation.

Recommended:

```text
React Hook Form
+
Zod
```

Validation should exist on the frontend for UX, but backend Pydantic validation remains authoritative.

---

# 32. Tables

All management tables should support:

- Server-side pagination.
- Search.
- Sorting.
- Filters.
- Loading state.
- Empty state.
- Error state.
- Row actions.
- Confirmation for destructive actions.

Avoid loading entire large tables into the browser.

---

# 33. Loading & Error UX

Every API screen should support:

```text
Loading
Success
Empty
Error
Unauthorized
Forbidden
```

Example:

```text
403:
You do not have permission to perform this action.
```

---

# 34. API Error Handling

Normalize FastAPI errors in the API client.

Example:

```ts
type ApiError = {
  success: false;
  error: {
    code: string;
    message: string;
  };
};
```

Display user-friendly messages.

Do not expose stack traces to users.

---

# 35. Route Protection

Protected routes:

```text
/admin/*
/admin/users/*
/admin/roles/*
/admin/permissions/*
/admin/exams/*
/admin/subjects/*
/admin/topics/*
/admin/questions/*
/admin/notifications/*
/admin/audit-logs/*
/admin/settings/*
/admin/profile/*
/notifications/*
/profile/*
```

Public:

```text
/login
/forgot-password
/reset-password
```

Unauthorized users:

```text
→ /login
```

Authenticated users without permission:

```text
→ /403
```

---

# 36. Suggested TypeScript Types

Example:

```ts
export interface User {
  id: number;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  status: string;
}

export interface Exam {
  id: number;
  name: string;
  code: string;
  description?: string;
  status: string;
}

export interface Question {
  id: number;
  subjectId: number;
  topicId: number | null;
  questionType: string;
  questionText: string;
  difficulty: string;
  status: string;
}
```

> The former `Test`, `Assignment`, `Attempt`, `Result` and report types were
> removed together with the test domain.

All backend numeric IDs should remain `number` on the frontend.

---

# 37. State Management

Do not introduce unnecessary global state.

Use:

```text
React state
+
API/server state
+
Context only for truly global UI state
```

Suitable global state:

```text
Authenticated user
Theme
Sidebar state
Notification count
```

Avoid putting every API entity into a global store.

---

# 38. No Cache Requirement

The application does not require Redis or a dedicated cache layer.

Frontend should also avoid implementing a complex persistent cache.

For list-heavy admin screens, the priority is reliable server synchronization rather than caching.

Temporary in-memory UI state is acceptable.

---

# 39. Security Requirements

Frontend:

- Use HTTPS.
- Avoid storing passwords.
- Prefer HttpOnly secure cookies for refresh/session credentials.
- Protect routes.
- Do not trust frontend permissions.
- Never expose question answer keys through read-only APIs.
- Do not expose internal API secrets.
- Sanitize/secure rich HTML content.
- Avoid dangerous `dangerouslySetInnerHTML` unless content is sanitized.
- Handle token expiration.
- Avoid sensitive information in browser logs.

---

# 40. Accessibility

Support:

- Keyboard navigation.
- Visible focus state.
- Semantic buttons.
- Accessible labels.
- Screen-reader-friendly form errors.
- Appropriate color contrast.
- Responsive layouts.

Status must not be conveyed by color alone.

---

# 41. Responsive Design

Target:

```text
Desktop
Tablet
Mobile browser
```

Priority:

1. Desktop admin experience.
2. Tablet.
3. Mobile experience.

The admin and student surfaces should remain usable on small screens.

---

# 42. Frontend Testing

> **Not included.** No unit/integration/E2E test framework is configured for the
> frontend; the project is verified with `npx tsc --noEmit` and `next build`.
> There is no test-player/scoring/timer surface left to test.

If tests are reintroduced, cover the surviving surface:

- Permission helpers.
- Form validation.
- UI components.
- API error mapping.
- Authentication and protected-route redirects.

---

# 43. Swagger Integration

Swagger belongs to the FastAPI backend:

```text
http://localhost:8000/docs
```

Frontend developers should use the OpenAPI definition as the source for API contracts.

Recommended development workflow:

```text
FastAPI Schema
      ↓
OpenAPI
      ↓
Frontend Type/API Client
      ↓
Next.js
```

If desired, TypeScript API types/client generation can later be automated from OpenAPI.

---

# 44. Frontend Development Commands

Example:

```bash
npm install
npm run dev
```

Production build:

```bash
npm run build
npm run start
```

Type-check / production build:

```bash
npx tsc --noEmit
npm run build
```

---

# 45. Recommended UI Modules

```text
Auth
Admin Dashboard
Users
Roles
Permissions
Exams
Subjects
Topics
Question Bank
Notifications
Audit Logs
Settings
Student Dashboard
Profile
```

> The former *Test Builder*, *Assignments*, *Attempt Monitor*, *Results*,
> *Reports*, *Student Test Player* and *Student History* modules were removed.

---

# 46. Frontend Definition of Done

MVP frontend is complete when:

- Login works.
- JWT/session integration works.
- Role-based routes work.
- Permission-based menus/actions work.
- Admin dashboard works.
- User management works.
- Role/permission management works.
- Exam management works.
- Subject/topic management works.
- Question bank works.
- Notifications, audit logs, settings and profile work.
- Admin dashboard works.
- API errors are handled.
- Responsive layout is implemented.
- The project type-checks (`npx tsc --noEmit`) and builds (`next build`).

> Test-builder, assignment, student-test-player, timer, autosave, submission,
> results and reports items were removed with the test domain.

---

# 47. Backend/Frontend Integration Contract

The backend owns:

```text
Authentication
Authorization
Business Rules
Data Integrity
```

The frontend owns:

```text
Presentation
Navigation
Forms
Client-side Validation
User Experience
Tables
```

Never move authoritative business rules into Next.js.

---

# 48. End-to-End Application Flow

```text
                 ADMIN
                   |
                   v
             Create Exam
                   |
                   v
            Create Subjects
                   |
                   v
             Create Topics
                   |
                   v
             Create Questions
                   |
                   v
        Publish Exam / Question
                   |
                   v
             STUDENT
                   |
                   v
        View notifications & profile
```

> The former test-assembly → assignment → attempt → submission → scoring →
> result → report flow was removed.

---

# 49. Recommended Implementation Order

## Sprint 1

```text
Backend project
PostgreSQL
SQLAlchemy
Alembic
Auth
JWT
Users
Roles
Permissions
Seed data
Swagger
```

## Sprint 2

```text
Exams
Subjects
Topics
Question Bank
Admin frontend
```

## Sprint 3

```text
Notifications
Audit Logs
Settings
Student Dashboard
Profile
```

## Sprint 4

```text
Deployment
Security review
Performance review
Monitoring
```

> The former sprints building the Test Builder, Assignments, Test Player, Timer,
> Autosave, Submission, Scoring, Results and Reports were dropped with the test
> domain.

---

# 50. Final Architecture Decision

The initial production architecture is intentionally simple:

```text
Next.js
   |
 HTTPS
   |
FastAPI
   |
SQLAlchemy ORM
   |
PostgreSQL
```

There is deliberately **no Redis/cache layer**.

This keeps the first release easier to deploy and maintain while leaving room to add caching later if actual performance measurements demonstrate a need.

The backend remains the authoritative source for authentication, authorization and business rules.

---

# 51. Import Test from XLSX — REMOVED

> **Removed.** The XLSX test-import feature (backend `/tests/import` +
> `/tests/import/template`, `test_import_service`, `app/utils/xlsx.py`, the
> `TestImportResponse` type, `testsApi.importXlsx` / `importTemplate`, the
> `/admin/upload` and `/admin/tests` UI, and `lib/test-import.ts`) has been
> deleted with the test domain.
>
> Questions can still be imported through the question-bank endpoint
> `POST /questions/import` (JSON), which is unrelated to the removed test
> import.

# Student Test Application — Frontend Technical Design & Development Specification

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
| Testing | Vitest/Jest + Playwright recommended |

---

# 2. Frontend Objective

The Next.js application will provide:

- Public authentication screens.
- Role-based dashboards.
- Student examination experience.
- Administrative management interfaces.
- Question-bank management.
- Test creation and scheduling.
- Results and analytics.
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
│   │   │   ├── tests/
│   │   │   ├── assignments/
│   │   │   ├── attempts/
│   │   │   ├── results/
│   │   │   ├── reports/
│   │   │   ├── notifications/
│   │   │   ├── audit-logs/
│   │   │   ├── settings/
│   │   │   └── profile/
│   │   │
│   │   ├── student/
│   │   │   ├── tests/
│   │   │   ├── attempts/
│   │   │   ├── results/
│   │   │   └── history/
│   │   │
│   │   └── layout.tsx
│   │
│   ├── components/
│   │   ├── ui/
│   │   ├── forms/
│   │   ├── tables/
│   │   ├── modals/
│   │   ├── charts/
│   │   └── test-player/
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
├── tests/
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
| Questions      |                                  |
| Tests          |                                  |
| Reports        |                                  |
| Users          |                                  |
+----------------+----------------------------------+
```

Sidebar items should be dynamically filtered by permissions.

---

# 11. Admin Dashboard

Display:

- Total users.
- Active students.
- Total exams.
- Published tests.
- Scheduled tests.
- Active attempts.
- Completed attempts.
- Average score.
- Pass percentage.
- Recent activities.

Dashboard APIs:

```text
GET /reports/dashboard
```

---

# 12. Student Dashboard

Display:

- Available exams.
- Upcoming tests.
- Tests in progress.
- Completed tests.
- Recent results.
- Average score.
- Subject performance.
- Notifications.

APIs:

```text
GET /student/tests
GET /student/attempts
GET /student/results
GET /notifications
```

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

Reset password calls `POST /users/{id}/reset-password` (requires the
`user.update` permission). With `{ "new_password": "…" }` the server validates
and applies it; with an empty body the server generates a temporary password
and returns it once in `temporary_password` for the admin to communicate
securely.

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

without redesigning the entire test player.

---

# 19. Test Builder

Routes:

```text
/tests
/tests/create
/tests/[id]
/tests/[id]/edit
```

Configuration:

```text
Exam
Test Name
Code
Instructions
Duration
Total Marks
Passing Marks
Negative Marking
Max Attempts
Randomize Questions
Randomize Options
Start Date/Time
End Date/Time
```

Question selection:

```text
Select individual questions
OR
Select question pool/rules
```

---

# 20. Test Publishing Workflow

```text
DRAFT
  |
  v
READY
  |
  v
PUBLISHED
  |
  v
SCHEDULED / ACTIVE
  |
  v
COMPLETED
  |
  v
ARCHIVED
```

Frontend should prevent invalid state transitions.

Backend remains authoritative.

Each transition maps to a backend action:

```text
DRAFT    -> READY      POST /tests/{id}/ready
READY    -> PUBLISHED  POST /tests/{id}/publish
PUBLISHED-> SCHEDULED  POST /tests/{id}/schedule   (scheduled_start_at required)
PUBLISHED/SCHEDULED -> ACTIVE  POST /tests/{id}/activate
PUBLISHED/SCHEDULED/ACTIVE -> COMPLETED  POST /tests/{id}/complete
COMPLETED/CLOSED -> ARCHIVED    POST /tests/{id}/archive
PUBLISHED -> CLOSED    POST /tests/{id}/close
```

Students may start an attempt while the test is `PUBLISHED`, `SCHEDULED`
(inside its window) or `ACTIVE`.

---

# 21. Assignment Management

Admin/examiner can assign tests to:

- Individual students.
- Student groups.
- Classes/batches.
- Eligible users.

UI:

```text
/tests/[id]/assign
```

Features:

- Search students.
- Multi-select.
- Set availability.
- Set attempt limit.
- Bulk assignment.
- Assignment status.

---

# 22. Student Test Player

Route:

```text
/student/attempts/[attemptId]
```

Layout:

```text
+------------------------------------------------------+
| Test Name                       Remaining Time       |
+----------------------+-------------------------------+
| Question Palette    | Question                       |
| 1 2 3 4 5 ...       |                               |
|                      | A. Option                     |
| Answered            | B. Option                     |
| Unanswered          | C. Option                     |
| Review               | D. Option                     |
+----------------------+-------------------------------+
| Previous | Mark Review | Save | Next                |
+------------------------------------------------------+
```

Features:

- Countdown timer.
- Question navigation.
- Answer selection.
- Mark for review.
- Clear answer.
- Autosave.
- Question palette.
- Final submission confirmation.
- Auto-submit on timeout.

---

# 23. Timer Requirements

The frontend timer is only a display mechanism.

The backend calculates:

```text
expires_at
```

The frontend calculates remaining display time from server-provided timestamps.

Never trust the browser timer for exam security.

---

# 24. Autosave

Student answers should be saved frequently.

Example:

```http
PUT /student/attempts/{attempt_id}/answers
```

Payload:

```json
{
  "question_id": 123,
  "selected_option_id": 456,
  "is_marked_for_review": false
}
```

UI should show:

```text
Saved
Saving...
Unable to save
```

A temporary network failure should not silently discard the student's answer.

---

# 25. Submission

Before submission:

```text
Are you sure you want to submit?
Answered: 45
Unanswered: 5
Marked for review: 3
```

Then:

```http
POST /student/attempts/{attempt_id}/submit
```

After successful submission:

```text
No further editing.
Redirect to result page or submission confirmation.
```

---

# 26. Result Screen

Route:

```text
/student/results/[id]
```

Display according to result-visibility rules:

```text
Score
Maximum Score
Percentage
Correct
Incorrect
Unanswered
Pass/Fail
Rank
Percentile
Time Used
```

Optional:

```text
Subject-wise performance
Question review
Correct answer
Explanation
```

Correct answers must only be shown when the backend allows them.

---

# 27. Student History

Route:

```text
/student/history
```

Columns:

```text
Test
Exam
Attempt
Date
Score
Percentage
Status
Action
```

Filters:

```text
Exam
Date
Status
```

---

# 28. Reports

Admin report screens:

```text
/reports
/reports/exams
/reports/tests
/reports/students
/reports/questions
/reports/subjects
```

Use tables and charts where useful.

Examples:

- Pass/fail distribution.
- Average score.
- Subject accuracy.
- Question difficulty performance.
- Student progress.

---

# 29. Export

Where backend provides export endpoints:

```text
CSV
Excel
PDF
```

Concrete backend CSV exports:

```text
GET /results/export                    (result.export)
GET /reports/exams/export              (report.export)
GET /reports/tests/export              (report.export)
GET /reports/students/{id}/export      (report.export)
GET /reports/questions/export          (report.export)
GET /reports/subjects/export           (report.export)
```

Frontend should trigger downloads through authenticated API calls.

Do not generate authoritative reports only on the frontend.

---

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
/dashboard/*
/users/*
/roles/*
/exams/*
/questions/*
/tests/*
/reports/*
/student/*
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

export interface Test {
  id: number;
  examId: number;
  name: string;
  durationMinutes: number;
  totalMarks: number;
  passingMarks: number;
  status: string;
}
```

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

For test attempts, the priority is reliable server synchronization rather than caching.

Temporary in-memory UI state is acceptable.

---

# 39. Security Requirements

Frontend:

- Use HTTPS.
- Avoid storing passwords.
- Prefer HttpOnly secure cookies for refresh/session credentials.
- Protect routes.
- Do not trust frontend permissions.
- Never expose answer keys before submission.
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

The test player must be usable without relying only on color.

---

# 41. Responsive Design

Target:

```text
Desktop
Tablet
Mobile browser
```

Priority:

1. Desktop test/admin experience.
2. Tablet.
3. Mobile student experience.

The student test player should remain usable on small screens.

---

# 42. Frontend Testing

## Unit Tests

Test:

- Permission helpers.
- Form validation.
- Scoring display.
- Timer calculation.
- UI components.
- API error mapping.

## Integration Tests

Test:

- Login.
- Protected routes.
- Role-based navigation.
- Test creation.
- Question creation.
- Student test flow.

## E2E

Recommended Playwright scenarios:

```text
Admin Login
Create Exam
Create Question
Create Test
Publish Test
Assign Student
Student Login
Start Test
Answer Questions
Submit Test
View Result
Admin View Report
```

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

Tests:

```bash
npm run test
npm run test:e2e
```

---

# 45. Recommended UI Modules

```text
Auth
Dashboard
Users
Roles
Permissions
Exams
Subjects
Topics
Question Bank
Test Builder
Assignments
Attempt Monitor
Results
Reports
Notifications
Audit Logs
Settings
Student Test Player
Student History
Profile
```

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
- Test builder works.
- Assignment works.
- Student test player works.
- Timer uses backend expiry information.
- Answers autosave.
- Submission works.
- Results display correctly.
- Reports display correctly.
- API errors are handled.
- Responsive layout is implemented.
- Critical E2E tests pass.

---

# 47. Backend/Frontend Integration Contract

The backend owns:

```text
Authentication
Authorization
Business Rules
Exam Eligibility
Timer Authority
Question Correctness
Scoring
Result Calculation
Data Integrity
```

The frontend owns:

```text
Presentation
Navigation
Forms
Client-side Validation
User Experience
Visual Timer
Tables
Charts
```

Never move authoritative business rules such as scoring or eligibility only into Next.js.

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
             Create Questions
                   |
                   v
              Create Test
                   |
                   v
             Publish Test
                   |
                   v
             Assign Students
                   |
                   v
              STUDENT
                   |
                   v
             View Test
                   |
                   v
              Start Test
                   |
                   v
              Answer Qs
                   |
                   v
              Submit Test
                   |
                   v
             FastAPI Scoring
                   |
                   v
                Result
                   |
                   v
           Student / Admin Reports
```

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
Test Builder
Assignments
Student Dashboard
```

## Sprint 4

```text
Test Player
Timer
Autosave
Submission
Scoring
```

## Sprint 5

```text
Results
Reports
Audit Logs
Notifications
```

## Sprint 6

```text
Security testing
Performance testing
E2E testing
Production deployment
Monitoring
```

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

The backend remains the authoritative source for authentication, authorization, exam rules, test timing, scoring and results.

---

# 51. Import Test from XLSX

## Objective
Enable admin/examiner users to create a new `DRAFT` test and its questions in one step by uploading a structured `.xlsx` workbook. Features: downloadable XLSX template, all-or-nothing validation with per-row errors, auto-creation of referenced `subjects`/`topics` inside the selected `exam`, and frontend UI in Admin → Tests.

## Backend Summary (for integration)
- `GET /api/v1/tests/import/template` returns `.xlsx` template (requires `test.create` and `question.create`).
- `POST /api/v1/tests/import` accepts `multipart/form-data` with `file` and `exam_id`; returns `TestImportResponse` on success (201). Errors: 404 `EXAM_NOT_FOUND`, 409 `TEST_CODE_EXISTS`, 422 `TEST_IMPORT_INVALID` with `details.errors` (list of `{row,field,message}`).
- Imported test and questions are created as `DRAFT`; `total_marks` recomputed from questions; `test.import` audit written.

## Frontend Implementation
- `frontend/src/lib/types.ts`: `TestImportResponse`.
- `frontend/src/lib/api/endpoints.ts`: `testsApi.importXlsx(FormData)`, `testsApi.importTemplate()` (download).
- `frontend/src/app/admin/tests/page.tsx`: Import XLSX button + modal. Modal includes exam select, file input, "Download template" button, scrollable per-row error list on validation failure, and success toast with created counts. Uses `downloadBlob`.

## Integration Contract Additions
- `POST /tests/import`: multipart; 201 TestImportResponse; 422 returns `error.details.errors` (array). Requires `test.create` and `question.create`.
- `GET /tests/import/template`: file download; requires `test.create` and `question.create`.

## Definition of Done (updates)
- Template downloadable and valid; import creates test+questions atomically with correct counts and DRAFT status.
- Auto-create subjects/topics inside selected exam works; re-import reuses existing.
- All-or-nothing validation returns per-row errors with clear messages; frontend displays them.
- UI handles upload, download, success/error; backend/frontend types/endpoints in sync.
- Tests cover happy path, conflicts, validation, permissions, template.

---

# 52. Question Tags, Test Lifecycle, Admin Password Reset & Report Exports

## Objective
Record the backend capabilities that were added on top of the original
specification and the frontend integration points they require. These extend
the Question Bank, Test Builder, User Management and Reports modules.

## Backend Summary (for integration)
- **Question tags.** `questions.tags` is a JSONB array of free-form labels.
  `QuestionCreate` / `QuestionUpdate` / `QuestionImportItem` accept `tags` and
  `QuestionResponse` returns them. `GET /questions?tag=<label>` filters by exact
  membership (combined with the existing subject/topic/type/difficulty/status
  filters). Requires `question.view` / `question.create` / `question.update`.
- **Test lifecycle.** `TestStatus` is `DRAFT`, `READY`, `PUBLISHED`,
  `SCHEDULED`, `ACTIVE`, `COMPLETED`, `CLOSED`, `ARCHIVED`. Action endpoints:
  `POST /tests/{id}/ready|publish|schedule|activate|complete|archive|close`
  (all require `test.publish`). `schedule` requires `scheduled_start_at`
  (400 `TEST_SCHEDULE_REQUIRED`). Students may start `PUBLISHED`, `SCHEDULED`
  (inside its window) and `ACTIVE` tests.
- **Admin password reset.** `POST /users/{id}/reset-password` requires
  `user.update`. Body `{ "new_password"?: string }`: when supplied it is
  strength-validated (400 `WEAK_PASSWORD`); when omitted the server generates a
  temporary password returned once in `temporary_password`.
- **Report CSV exports.** `GET /reports/exams/export`, `/reports/tests/export`,
  `/reports/questions/export`, `/reports/subjects/export` and
  `/reports/students/{id}/export` return `text/csv` attachments and require the
  `report.export` permission (`report.view` still guards the JSON variants).

## Frontend Implementation
- `frontend/src/lib/types.ts`: add `tags?: string[]` to the question types;
  widen the `TestStatus` union; add `UserPasswordResetResponse`, `TestStatus`
  transition helpers and the report/export row types.
- `frontend/src/lib/api/endpoints.ts`: add the `testsApi` lifecycle action
  methods, `usersApi.resetPassword(...)`, the `questionsApi` `tag` filter, and
  the `reportsApi` CSV download methods (return blobs via the authenticated
  client).
- Tests module: show only the lifecycle actions legal for the current status
  and trigger them through the new endpoints; students see the test as
  startable for `PUBLISHED` / `SCHEDULED` / `ACTIVE`.
- Users module: "Reset password" action opening a dialog that either sets a
  password or generates a temporary one, displaying it once.
- Question Bank: add the Tag filter and a Tags input in the editor.
- Reports: add CSV export buttons and charts/tables as described in §28.

## Integration Contract Additions
- `POST /tests/{id}/ready|publish|schedule|activate|complete|archive|close`:
  `200 TestResponse`; `409` state conflicts; `400 TEST_HAS_NO_QUESTIONS` /
  `TEST_SCHEDULE_REQUIRED`. Requires `test.publish`.
- `POST /users/{id}/reset-password`: `200 UserPasswordResetResponse`; `400`
  `WEAK_PASSWORD`; `404 USER_NOT_FOUND`. Requires `user.update`.
- `GET /questions?tag=`: `200 Page<QuestionResponse>`. Requires `question.view`.
- `GET /reports/*/export`: `text/csv` attachment. Requires `report.export`.

## Definition of Done (updates)
- Question tags round-trip through create/update/import and filter the listing.
- Every lifecycle transition is enforced by the backend and surfaced correctly
  by the UI; invalid actions are hidden.
- Admins can reset a password (explicit or generated) and see the temporary
  password once.
- Report exports download as CSV through authenticated calls and require
  `report.export`.

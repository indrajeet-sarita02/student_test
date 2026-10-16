"""API v1 router aggregation.

Every module under ``app/api/v1`` exposes ``router`` with routes relative to
its own prefix; this module attaches the prefixes and is mounted at
``/api/v1`` by ``app.main``.
"""

from fastapi import APIRouter

from app.api.v1 import (
    assignments,
    attempts,
    audit_logs,
    auth,
    exams,
    notifications,
    permissions,
    questions,
    reports,
    results,
    roles,
    settings,
    student,
    subjects,
    tests,
    topics,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])
api_router.include_router(exams.router, prefix="/exams", tags=["Exams"])
api_router.include_router(subjects.router, prefix="/subjects", tags=["Subjects"])
api_router.include_router(topics.router, prefix="/topics", tags=["Topics"])
api_router.include_router(questions.router, prefix="/questions", tags=["Questions"])
api_router.include_router(tests.router, prefix="/tests", tags=["Tests"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])
api_router.include_router(attempts.router, prefix="/attempts", tags=["Attempts (Admin)"])
api_router.include_router(results.router, prefix="/results", tags=["Results"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(student.router, prefix="/student", tags=["Student Test APIs"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])

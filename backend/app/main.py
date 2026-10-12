"""FastAPI application entry point: ``uvicorn app.main:app --reload``."""

import logging
import time
import uuid
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.routing import Match
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.db.session import engine

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("student_test")

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "REST API for the Student Test Application: authentication, RBAC, exam & "
        "question management, test assembly, assignment, test taking, scoring, "
        "results and reports."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _route_exists(path: str, method: str) -> bool:
    """True when a registered route answers ``path``.

    ``Match.PARTIAL`` (right path, wrong method) counts as existing: swapping
    the slash must not turn a would-be 405 into a 404, and must not hide a
    redirect that Starlette would otherwise issue.
    """
    probe: Dict[str, Any] = {"type": "http", "path": path, "root_path": "", "method": method}
    for route in app.routes:
        if route.matches(probe)[0] is not Match.NONE:
            return True
    return False


class TrailingSlashNormalizer:
    """Serve ``/subjects`` and ``/subjects/`` from the same route.

    Starlette's router answers a trailing-slash mismatch with a **307** to the
    other spelling, so every list call the frontend makes without a trailing
    slash (``GET /api/v1/subjects?page=1``) costs an extra round-trip and shows
    up as a redirect in the browser's network panel. This middleware performs
    the identical path swap *before* routing instead, so both spellings are
    served directly and the API never issues a trailing-slash redirect.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            path = scope.get("path", "")
            if path and path != "/":
                method = scope.get("method", "GET")
                if not _route_exists(path, method):
                    alternate = path + "/" if not path.endswith("/") else path.rstrip("/") or "/"
                    if alternate != path and _route_exists(alternate, method):
                        scope["path"] = alternate
        await self.app(scope, receive, send)


# Registered last -> outermost, so the normalised path is what the router,
# the logger below and the CORS middleware all see.
app.add_middleware(TrailingSlashNormalizer)


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Attach a request id, log method/path/status/duration (never bodies)."""
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s -> %s in %.1fms [%s]",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_payload())


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error.get("loc", []) if part != "body")
        details.append({"field": field or "body", "message": error.get("msg", "Invalid value")})
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": details,
            },
        },
    )


_STATUS_CODES: Dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _STATUS_CODES.get(exc.status_code, f"HTTP_{exc.status_code}")
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": code, "message": message}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "-")
    logger.exception("Unhandled error [%s] on %s %s", request_id, request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."},
        },
    )


@app.get("/", tags=["Health"], summary="API root")
async def root() -> Dict[str, Any]:
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "api": "/api/v1",
    }


@app.get("/health", tags=["Health"], summary="Health check", description="Verifies API and database reachability.")
async def health() -> Dict[str, Any]:
    status = "ok"
    database = "up"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - depends on DB availability
        status = "degraded"
        database = "down"
        logger.exception("Database health check failed")
    return {"status": status, "database": database, "environment": settings.app_env}


app.include_router(api_router, prefix="/api/v1")

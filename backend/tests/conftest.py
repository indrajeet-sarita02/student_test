"""Pytest fixtures.

The integration tests use a dedicated PostgreSQL schema so the application's
real data is never touched. If the schema cannot be created (restricted
credentials / no server), DB-backed tests are skipped and the pure unit tests
still run.
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  (populate Base.metadata)
from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app

# A per-process schema name means two concurrent test runs against the same
# database can never ``DROP``/recreate each other's schema mid-run.
TEST_SCHEMA = f"student_test_pytest_{os.getpid()}"


@pytest.fixture(scope="session")
def _admin_engine():
    engine = create_engine(settings.database_url, future=True)
    try:
        # Always start from a clean schema so leftover state from an aborted
        # run can never collide with ``Base.metadata.create_all``.
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE'))
            conn.execute(text(f'CREATE SCHEMA "{TEST_SCHEMA}"'))
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"PostgreSQL test schema unavailable: {exc}")
        return
    yield engine
    with engine.begin() as conn:
        conn.execute(text(f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE'))
    engine.dispose()


@pytest.fixture(scope="session")
def engine(_admin_engine):
    test_engine = create_engine(settings.database_url, future=True)

    # The Prisma Postgres pooler cannot be relied on to preserve a
    # session-level ``search_path`` across a long test run, so compile the
    # schema directly into every statement instead.  ``MetaData.schema`` does
    # not retroactively apply to already-declared tables, hence the loop.
    Base.metadata.schema = TEST_SCHEMA
    for table in Base.metadata.tables.values():
        table.schema = TEST_SCHEMA

    # The schema was just dropped/recreated by ``_admin_engine``, so it is
    # guaranteed empty and the existence probe can be skipped.
    Base.metadata.create_all(test_engine, checkfirst=False)
    yield test_engine
    test_engine.dispose()

    # Restore the shared metadata so nothing outside this session is affected.
    Base.metadata.schema = None
    for table in Base.metadata.tables.values():
        table.schema = None


@pytest.fixture(scope="session")
def session_factory(engine):
    return sessionmaker(bind=engine, class_=Session, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def _seed(session_factory):
    """Seed the test schema once using the same idempotent seed script."""
    from scripts import seed as seed_script

    session = session_factory()
    try:
        seed_script.run_seed(session)
    finally:
        session.close()
    yield


@pytest.fixture
def db(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    """TestClient whose DB dependency is bound to the test schema."""

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _login(client: TestClient, username: str, password: str = "Admin@123") -> str:
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(client: TestClient, username: str, password: str = "Admin@123") -> dict:
    return {"Authorization": f"Bearer {_login(client, username, password)}"}


@pytest.fixture
def admin_headers(client):
    return auth_headers(client, "admin@example.com")


@pytest.fixture
def superadmin_headers(client):
    return auth_headers(client, "superadmin@example.com")


@pytest.fixture
def student_headers(client):
    return auth_headers(client, "student@example.com")


@pytest.fixture
def unique() -> str:
    return uuid.uuid4().hex[:8].upper()


@pytest.fixture
def create_user(db):
    """Factory creating an active user with a hashed password."""

    def _create(username: str, password: str = "Admin@123", **kwargs):
        from app.models.user import User
        from app.utils.enums import UserStatus

        user = User(
            username=username,
            email=kwargs.pop("email", f"{username}@example.com"),
            password_hash=hash_password(password),
            first_name=kwargs.pop("first_name", username.title()),
            status=UserStatus.ACTIVE.value,
            is_verified=True,
            **kwargs,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _create

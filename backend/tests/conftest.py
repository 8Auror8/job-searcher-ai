"""Test fixtures.

Uses in-memory SQLite by default (no Docker needed). CI sets TEST_DATABASE_URL to a real
PostgreSQL service so the same tests run against the production database engine.
"""

import os
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.setdefault("ENVIRONMENT", "test")

from app.api import deps
from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.core.rate_limit import limiter
from app.main import create_app
from app.models import Base
from app.schemas.cv import CvProfile
from app.services.cv_extraction import AiUnavailable, ExtractionResult
from app.services.google_oauth import (
    AuthorizationRequest,
    GoogleIdentity,
    GoogleOAuthError,
)
from app.services.mailer import Email

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
PASSWORD = "correct horse battery"


@dataclass
class FakeMailer:
    sent: list[Email] = field(default_factory=list)

    async def send(self, email: Email) -> None:
        self.sent.append(email)

    def last_token(self) -> str:
        match = re.search(r"token=([\w-]+)", self.sent[-1].text)
        assert match, "no token in last email"
        return match.group(1)


@dataclass
class FakeGoogle:
    identity: GoogleIdentity | None = None
    fail: bool = False

    def build_authorization(self) -> AuthorizationRequest:
        return AuthorizationRequest(
            "https://accounts.google.com/o/oauth2/v2/auth?fake=1", "state-123", "verifier", "n-1"
        )

    async def fetch_identity(self, code: str, code_verifier: str) -> GoogleIdentity:
        if self.fail or self.identity is None:
            raise GoogleOAuthError("boom")
        return self.identity


@dataclass
class FakeExtractor:
    model: str = "fake-model"
    fail: bool = False
    calls: int = 0
    profile: CvProfile = field(
        default_factory=lambda: CvProfile(
            full_name="Laura Gomez Ruiz",
            skills=["Python", "FastAPI", "Kubernetes"],  # Kubernetes is NOT in the test CV
        )
    )

    async def extract(self, text: str, origin: str) -> ExtractionResult:
        self.calls += 1
        if self.fail:
            raise AiUnavailable()
        return ExtractionResult(self.profile.model_copy(deep=True), self.model, 100, 50, 5)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,  # never read the developer's local .env in tests
        environment="test",
        database_url=TEST_DATABASE_URL,
        frontend_url="http://app.test",
        google_client_id="client-id",
        google_client_secret="client-secret",
    )


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    kwargs = (
        {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
        if TEST_DATABASE_URL.startswith("sqlite")
        else {}
    )
    engine = create_async_engine(TEST_DATABASE_URL, **kwargs)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def mailer() -> FakeMailer:
    return FakeMailer()


@pytest.fixture
def google() -> FakeGoogle:
    return FakeGoogle()


@pytest.fixture
def extractor() -> FakeExtractor:
    return FakeExtractor()


@pytest.fixture
async def client(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    mailer: FakeMailer,
    google: FakeGoogle,
    extractor: FakeExtractor,
) -> AsyncIterator[AsyncClient]:
    app = create_app(settings)

    async def _session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[deps.get_mailer] = lambda: mailer
    app.dependency_overrides[deps.get_google_client] = lambda: google
    app.dependency_overrides[deps.get_cv_extractor] = lambda: extractor
    limiter.reset()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c


def csrf(client: AsyncClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("csrf_token") or ""}


async def register_and_verify(
    client: AsyncClient, mailer: FakeMailer, email: str = "ana@example.com"
) -> None:
    resp = await client.post(
        "/api/auth/register", json={"email": email, "password": PASSWORD, "accept_terms": True}
    )
    assert resp.status_code == 202
    resp = await client.post("/api/auth/verify-email", json={"token": mailer.last_token()})
    assert resp.status_code == 200


async def login(client: AsyncClient, email: str = "ana@example.com", password: str = PASSWORD):  # type: ignore[no-untyped-def]
    return await client.post("/api/auth/login", json={"email": email, "password": password})

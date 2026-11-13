from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import User
from app.services.google_oauth import GoogleIdentity
from tests.conftest import PASSWORD, FakeGoogle, FakeMailer, login, register_and_verify


def identity(email: str = "ana@example.com", verified: bool = True) -> GoogleIdentity:
    return GoogleIdentity(sub="google-sub-1", email=email, email_verified=verified, nonce="n-1")


async def start_login(client: AsyncClient) -> None:
    resp = await client.get("/api/auth/google/login")
    assert resp.status_code == 302
    assert resp.headers["location"].startswith("https://accounts.google.com/")
    assert "g_oauth" in client.cookies


async def test_google_creates_verified_user(client: AsyncClient, google: FakeGoogle) -> None:
    google.identity = identity()
    await start_login(client)
    resp = await client.get("/api/auth/google/callback?code=abc&state=state-123")
    assert resp.status_code == 302
    assert resp.headers["location"] == "http://app.test/app"
    me = (await client.get("/api/users/me")).json()
    assert me["is_verified"] is True
    assert me["google_linked"] is True
    assert me["has_password"] is False


async def test_google_rejects_state_mismatch(client: AsyncClient, google: FakeGoogle) -> None:
    google.identity = identity()
    await start_login(client)
    resp = await client.get("/api/auth/google/callback?code=abc&state=forged")
    assert resp.headers["location"] == "http://app.test/login?error=google"
    assert (await client.get("/api/users/me")).status_code == 401


async def test_google_without_state_cookie_fails(client: AsyncClient, google: FakeGoogle) -> None:
    google.identity = identity()
    resp = await client.get("/api/auth/google/callback?code=abc&state=state-123")
    assert resp.headers["location"].endswith("/login?error=google")


async def test_google_rejects_unverified_email(client: AsyncClient, google: FakeGoogle) -> None:
    google.identity = identity(verified=False)
    await start_login(client)
    resp = await client.get("/api/auth/google/callback?code=abc&state=state-123")
    assert resp.headers["location"].endswith("/login?error=google")


async def test_google_exchange_failure(client: AsyncClient, google: FakeGoogle) -> None:
    google.fail = True
    await start_login(client)
    resp = await client.get("/api/auth/google/callback?code=abc&state=state-123")
    assert resp.headers["location"].endswith("/login?error=google")


async def test_google_links_existing_verified_account(
    client: AsyncClient, google: FakeGoogle, mailer: FakeMailer
) -> None:
    await register_and_verify(client, mailer)
    google.identity = identity()
    await start_login(client)
    await client.get("/api/auth/google/callback?code=abc&state=state-123")
    me = (await client.get("/api/users/me")).json()
    assert me["google_linked"] is True and me["has_password"] is True


async def test_google_drops_password_of_unverified_preregistration(
    client: AsyncClient,
    google: FakeGoogle,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    # An attacker pre-registers the victim's email with a password they know.
    await client.post(
        "/api/auth/register",
        json={"email": "ana@example.com", "password": PASSWORD, "accept_terms": True},
    )
    google.identity = identity()
    await start_login(client)
    await client.get("/api/auth/google/callback?code=abc&state=state-123")

    async with session_factory() as s:
        user = await s.scalar(select(User).where(User.email == "ana@example.com"))
    assert user is not None and user.password_hash is None
    client.cookies.clear()
    assert (await login(client)).status_code == 401


async def test_google_disabled_returns_404(client: AsyncClient) -> None:
    from app.api import deps

    app = client._transport.app  # type: ignore[attr-defined]
    del app.dependency_overrides[deps.get_google_client]
    app.dependency_overrides[deps.get_settings] = lambda: deps.Settings(
        _env_file=None, environment="test"
    )
    resp = await client.get("/api/auth/google/login")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "feature_disabled"

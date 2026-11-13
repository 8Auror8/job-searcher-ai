"""Registration, verification, login, session refresh and logout."""

from datetime import timedelta

from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import utcnow
from app.models import OneTimeToken, RefreshToken
from tests.conftest import PASSWORD, FakeMailer, csrf, login, register_and_verify


async def test_full_happy_path(client: AsyncClient, mailer: FakeMailer) -> None:
    await register_and_verify(client, mailer)
    resp = await login(client)
    assert resp.status_code == 200
    assert resp.json()["email"] == "ana@example.com"
    assert {"access_token", "refresh_token", "csrf_token"} <= set(client.cookies.keys())

    me = await client.get("/api/users/me")
    assert me.status_code == 200
    body = me.json()
    assert body["is_verified"] is True
    assert body["has_password"] is True
    assert body["google_linked"] is False


async def test_email_is_normalized(client: AsyncClient, mailer: FakeMailer) -> None:
    await register_and_verify(client, mailer, email="  Ana@Example.COM ")
    assert (await login(client, email="ana@example.com")).status_code == 200


async def test_register_validation(client: AsyncClient) -> None:
    short = await client.post(
        "/api/auth/register", json={"email": "a@b.com", "password": "short", "accept_terms": True}
    )
    assert short.status_code == 422
    assert short.json()["error"]["code"] == "validation_error"

    no_terms = await client.post(
        "/api/auth/register",
        json={"email": "a@b.com", "password": PASSWORD, "accept_terms": False},
    )
    assert no_terms.status_code == 422

    bad_email = await client.post(
        "/api/auth/register", json={"email": "nope", "password": PASSWORD, "accept_terms": True}
    )
    assert bad_email.status_code == 422


async def test_register_does_not_reveal_existing_accounts(
    client: AsyncClient, mailer: FakeMailer
) -> None:
    await register_and_verify(client, mailer)
    payload = {"email": "ana@example.com", "password": "another password!", "accept_terms": True}
    first = await client.post("/api/auth/register", json={**payload, "email": "new@example.com"})
    second = await client.post("/api/auth/register", json=payload)
    assert first.status_code == second.status_code == 202
    assert first.json() == second.json()
    # The real owner is told by email instead, and the old password still works.
    assert mailer.sent[-1].subject.startswith("Intento de registro")
    assert (await login(client)).status_code == 200


async def test_login_requires_verified_email(client: AsyncClient, mailer: FakeMailer) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "ana@example.com", "password": PASSWORD, "accept_terms": True},
    )
    resp = await login(client)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "email_not_verified"


async def test_login_errors_are_generic(client: AsyncClient, mailer: FakeMailer) -> None:
    await register_and_verify(client, mailer)
    wrong_password = await login(client, password="wrong password!!")
    unknown_user = await login(client, email="ghost@example.com")
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


async def test_verification_token_single_use_and_expiry(
    client: AsyncClient,
    mailer: FakeMailer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "ana@example.com", "password": PASSWORD, "accept_terms": True},
    )
    token = mailer.last_token()

    async with session_factory() as s:
        await s.execute(update(OneTimeToken).values(expires_at=utcnow() - timedelta(minutes=1)))
        await s.commit()
    expired = await client.post("/api/auth/verify-email", json={"token": token})
    assert expired.status_code == 400

    await client.post("/api/auth/resend-verification", json={"email": "ana@example.com"})
    fresh = mailer.last_token()
    assert (await client.post("/api/auth/verify-email", json={"token": fresh})).status_code == 200
    reused = await client.post("/api/auth/verify-email", json={"token": fresh})
    assert reused.status_code == 400
    assert reused.json()["error"]["code"] == "invalid_token"


async def test_me_requires_authentication(client: AsyncClient) -> None:
    resp = await client.get("/api/users/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "not_authenticated"


async def test_refresh_rotates_and_detects_reuse(
    client: AsyncClient,
    mailer: FakeMailer,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await register_and_verify(client, mailer)
    await login(client)
    old_refresh = client.cookies.get("refresh_token")

    resp = await client.post("/api/auth/refresh", headers=csrf(client))
    assert resp.status_code == 200
    new_refresh = client.cookies.get("refresh_token")
    assert new_refresh and new_refresh != old_refresh

    # An attacker replays the old (rotated) token → whole family is revoked.
    client.cookies.set("refresh_token", old_refresh or "", path="/api/auth")
    replay = await client.post("/api/auth/refresh", headers=csrf(client))
    assert replay.status_code == 401

    async with session_factory() as s:
        tokens = (await s.scalars(select(RefreshToken))).all()
    assert tokens and all(t.revoked_at is not None for t in tokens)


async def test_logout_revokes_session(client: AsyncClient, mailer: FakeMailer) -> None:
    await register_and_verify(client, mailer)
    await login(client)
    refresh_token = client.cookies.get("refresh_token")
    headers = csrf(client)

    resp = await client.post("/api/auth/logout", headers=headers)
    assert resp.status_code == 200
    assert "access_token" not in client.cookies
    assert (await client.get("/api/users/me")).status_code == 401

    client.cookies.set("refresh_token", refresh_token or "", path="/api/auth")
    client.cookies.set("csrf_token", headers["X-CSRF-Token"])
    assert (await client.post("/api/auth/refresh", headers=headers)).status_code == 401


async def test_refresh_without_cookie(client: AsyncClient) -> None:
    assert (await client.post("/api/auth/refresh")).status_code == 401

from httpx import AsyncClient

from tests.conftest import FakeMailer, csrf, login, register_and_verify

NEW_PASSWORD = "a brand new passphrase"


async def test_reset_password_flow_closes_sessions(client: AsyncClient, mailer: FakeMailer) -> None:
    await register_and_verify(client, mailer)
    await login(client)
    headers = csrf(client)

    resp = await client.post(
        "/api/auth/password/forgot", json={"email": "ana@example.com"}, headers=headers
    )
    assert resp.status_code == 202
    token = mailer.last_token()

    reset = await client.post(
        "/api/auth/password/reset",
        json={"token": token, "password": NEW_PASSWORD},
        headers=headers,
    )
    assert reset.status_code == 200
    # Old sessions no longer refresh.
    assert (await client.post("/api/auth/refresh", headers=csrf(client))).status_code == 401
    assert (await login(client)).status_code == 401
    assert (await login(client, password=NEW_PASSWORD)).status_code == 200

    again = await client.post(
        "/api/auth/password/reset",
        json={"token": token, "password": NEW_PASSWORD},
        headers=csrf(client),
    )
    assert again.status_code == 400


async def test_forgot_password_unknown_email_is_silent(
    client: AsyncClient, mailer: FakeMailer
) -> None:
    resp = await client.post("/api/auth/password/forgot", json={"email": "ghost@example.com"})
    assert resp.status_code == 202
    assert mailer.sent == []


async def test_reset_rejects_short_password(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/auth/password/reset", json={"token": "x" * 20, "password": "short"}
    )
    assert resp.status_code == 422

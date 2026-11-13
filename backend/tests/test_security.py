"""Cross-cutting security behaviour: CSRF, rate limiting, headers, tokens, settings."""

import uuid
from datetime import timedelta

import jwt
import pytest
from httpx import AsyncClient

from app.core import security
from app.core.config import Settings
from app.core.db import utcnow
from tests.conftest import FakeMailer, csrf, login, register_and_verify


async def test_csrf_required_for_unsafe_requests_with_session(
    client: AsyncClient, mailer: FakeMailer
) -> None:
    await register_and_verify(client, mailer)
    await login(client)
    missing = await client.post("/api/auth/logout")
    assert missing.status_code == 403
    assert missing.json()["error"]["code"] == "csrf_failed"
    wrong = await client.post("/api/auth/logout", headers={"X-CSRF-Token": "nope"})
    assert wrong.status_code == 403
    assert (await client.post("/api/auth/logout", headers=csrf(client))).status_code == 200


async def test_login_is_rate_limited(client: AsyncClient) -> None:
    statuses = [
        (await login(client, email="x@example.com", password="whatever")).status_code
        for _ in range(11)
    ]
    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429


async def test_security_headers_and_request_id(client: AsyncClient) -> None:
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "ok"}
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Request-ID"]


def test_password_hashing() -> None:
    hashed = security.hash_password("secret passphrase")
    assert hashed.startswith("$argon2id$")
    assert security.verify_password("secret passphrase", hashed)
    assert not security.verify_password("other", hashed)
    assert not security.verify_password("x", "not-a-hash")


def test_access_token_roundtrip_and_rejections() -> None:
    settings = Settings(_env_file=None, environment="test")
    user_id = uuid.uuid4()
    token = security.create_access_token(user_id, settings)
    assert security.decode_access_token(token, settings) == user_id

    other = Settings(
        _env_file=None, environment="test", jwt_secret="another-secret-that-is-long-enough-123"
    )
    assert security.decode_access_token(token, other) is None

    expired = jwt.encode(
        {"sub": str(user_id), "type": "access", "exp": utcnow() - timedelta(seconds=1)},
        settings.jwt_secret,
        algorithm="HS256",
    )
    assert security.decode_access_token(expired, settings) is None

    wrong_type = jwt.encode(
        {"sub": str(user_id), "type": "oauth_state", "exp": utcnow() + timedelta(minutes=1)},
        settings.jwt_secret,
        algorithm="HS256",
    )
    assert security.decode_access_token(wrong_type, settings) is None


def test_oauth_state_roundtrip() -> None:
    settings = Settings(_env_file=None, environment="test")
    signed = security.sign_state({"state": "s", "verifier": "v"}, settings)
    assert security.read_state(signed, settings) == {"state": "s", "verifier": "v"}
    assert security.read_state("garbage", settings) is None


def test_production_settings_are_validated() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(_env_file=None, environment="production", cookie_secure=True)
    with pytest.raises(ValueError, match="COOKIE_SECURE"):
        Settings(_env_file=None, environment="production", jwt_secret="x" * 40, cookie_secure=False)
    ok = Settings(_env_file=None, environment="production", jwt_secret="x" * 40, cookie_secure=True)
    assert ok.is_production


def test_token_hash_is_deterministic_and_not_reversible() -> None:
    raw = security.generate_token()
    assert security.hash_token(raw) == security.hash_token(raw)
    assert raw not in security.hash_token(raw)

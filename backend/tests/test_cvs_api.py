"""CV versions API: upload, AI extraction, versions, profile edits, preferences, authorization."""

from typing import Any

from httpx import AsyncClient, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import AiUsage, Consent
from tests.conftest import FakeExtractor, FakeMailer, csrf, login, register_and_verify
from tests.factories import CV_PDF, LINKEDIN_PDF


async def sign_in(client: AsyncClient, mailer: FakeMailer, email: str = "ana@example.com") -> None:
    client.cookies.clear()
    await register_and_verify(client, mailer, email)
    assert (await login(client, email=email)).status_code == 200


async def upload(
    client: AsyncClient,
    data: bytes = CV_PDF,
    consent: bool = True,
    origin: str = "upload",
    filename: str = "cv.pdf",
    **form: Any,
) -> Response:
    return await client.post(
        "/api/cvs",
        files={"file": (filename, data, "application/pdf")},
        data={"consent": str(consent).lower(), "origin": origin, **form},
        headers=csrf(client),
    )


async def test_upload_extracts_and_grounds_profile(
    client: AsyncClient,
    mailer: FakeMailer,
    extractor: FakeExtractor,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await sign_in(client, mailer)
    resp = await upload(client, name="CV Backend")
    assert resp.status_code == 201, resp.text
    cv = resp.json()

    assert cv["name"] == "CV Backend"
    assert cv["is_primary"] is True  # first CV becomes the primary one
    assert cv["extraction_status"] == "ok"
    assert cv["profile"]["full_name"] == "Laura Gomez Ruiz"
    # The invented skill was removed and reported, never shown as fact.
    assert cv["profile"]["skills"] == ["Python", "FastAPI"]
    assert cv["extraction_notes"]["unverified"] == [{"field": "skills", "value": "Kubernetes"}]
    assert cv["extraction_notes"]["prompt_version"] == "cv_extraction_v1"
    assert extractor.calls == 1

    async with session_factory() as s:
        usage = (await s.scalars(select(AiUsage))).all()
        consents = (await s.scalars(select(Consent))).all()
    assert len(usage) == 1 and usage[0].input_tokens == 100
    assert len(consents) == 1 and consents[0].policy_version == "2026-11"


async def test_consent_is_required_once(client: AsyncClient, mailer: FakeMailer) -> None:
    await sign_in(client, mailer)
    resp = await upload(client, consent=False)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "consent_required"
    assert (await upload(client, consent=True)).status_code == 201
    # Already granted: later uploads don't need the checkbox again.
    assert (await upload(client, consent=False)).status_code == 201


async def test_linkedin_import(client: AsyncClient, mailer: FakeMailer) -> None:
    await sign_in(client, mailer)
    resp = await upload(client, LINKEDIN_PDF, origin="linkedin_pdf", filename="Profile.pdf")
    assert resp.status_code == 201
    assert resp.json()["origin"] == "linkedin_pdf"
    assert resp.json()["name"] == "Perfil de LinkedIn"


async def test_rejects_non_cv_files(client: AsyncClient, mailer: FakeMailer) -> None:
    await sign_in(client, mailer)
    resp = await upload(client, b"MZ\x90\x00 executable", filename="cv.pdf")
    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "unsupported_file"


async def test_without_ai_the_profile_is_manual(
    client: AsyncClient, mailer: FakeMailer, extractor: FakeExtractor
) -> None:
    from app.api import deps

    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[deps.get_cv_extractor] = lambda: None
    await sign_in(client, mailer)
    cv = (await upload(client)).json()
    assert cv["extraction_status"] == "manual"
    assert cv["extraction_notes"] == {"reason": "ai_disabled"}
    assert cv["has_source_text"] is True
    assert extractor.calls == 0


async def test_ai_failure_keeps_the_version_and_allows_retry(
    client: AsyncClient, mailer: FakeMailer, extractor: FakeExtractor
) -> None:
    await sign_in(client, mailer)
    extractor.fail = True
    cv = (await upload(client)).json()
    assert cv["extraction_status"] == "failed"

    retry = await client.post(f"/api/cvs/{cv['id']}/extract", headers=csrf(client))
    assert retry.status_code == 503
    extractor.fail = False
    retry = await client.post(f"/api/cvs/{cv['id']}/extract", headers=csrf(client))
    assert retry.status_code == 200
    assert retry.json()["extraction_status"] == "ok"


async def test_daily_ai_quota(
    client: AsyncClient,
    mailer: FakeMailer,
    settings: Any,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    settings.ai_daily_calls_per_user = 1
    await sign_in(client, mailer)
    first = (await upload(client)).json()
    assert first["extraction_status"] == "ok"
    second = (await upload(client)).json()
    assert second["extraction_status"] == "failed"
    assert second["extraction_notes"]["reason"] == "ai_quota_exceeded"
    retry = await client.post(f"/api/cvs/{first['id']}/extract", headers=csrf(client))
    assert retry.status_code == 429
    async with session_factory() as s:
        assert await s.scalar(select(func.count()).select_from(AiUsage)) == 1


async def test_versions_primary_archive_and_delete(client: AsyncClient, mailer: FakeMailer) -> None:
    await sign_in(client, mailer)
    a = (await upload(client, name="A")).json()
    b = (await client.post("/api/cvs/blank", json={"name": "B"}, headers=csrf(client))).json()
    assert b["origin"] == "manual" and b["is_primary"] is False

    resp = await client.patch(
        f"/api/cvs/{b['id']}", json={"is_primary": True}, headers=csrf(client)
    )
    assert resp.json()["is_primary"] is True
    listing = (await client.get("/api/cvs")).json()
    assert [cv["name"] for cv in listing] == ["B", "A"]
    assert [cv["is_primary"] for cv in listing] == [True, False]

    # Archiving the primary promotes the other one.
    await client.patch(f"/api/cvs/{b['id']}", json={"archived": True}, headers=csrf(client))
    listing = (await client.get("/api/cvs")).json()
    assert [(cv["name"], cv["is_primary"]) for cv in listing] == [("A", True)]
    with_archived = (await client.get("/api/cvs?include_archived=true")).json()
    assert len(with_archived) == 2

    rename = await client.patch(f"/api/cvs/{a['id']}", json={"name": "Nuevo"}, headers=csrf(client))
    assert rename.json()["name"] == "Nuevo"

    assert (await client.delete(f"/api/cvs/{a['id']}", headers=csrf(client))).status_code == 204
    assert (await client.get(f"/api/cvs/{a['id']}")).status_code == 404


async def test_edit_profile(client: AsyncClient, mailer: FakeMailer) -> None:
    await sign_in(client, mailer)
    cv = (await upload(client)).json()
    profile = cv["profile"] | {"headline": "Staff Engineer", "skills": ["Python", "Rust"]}
    resp = await client.put(f"/api/cvs/{cv['id']}/profile", json=profile, headers=csrf(client))
    assert resp.status_code == 200
    body = resp.json()
    assert body["profile"]["headline"] == "Staff Engineer"
    assert body["profile"]["skills"] == ["Python", "Rust"]  # the user may add anything
    assert body["extraction_notes"]["edited_by_user"] is True

    bad = await client.put(
        f"/api/cvs/{cv['id']}/profile",
        json={"total_years_experience": -3},
        headers=csrf(client),
    )
    assert bad.status_code == 422


async def test_users_cannot_access_other_users_cvs(client: AsyncClient, mailer: FakeMailer) -> None:
    await sign_in(client, mailer, "ana@example.com")
    cv_id = (await upload(client)).json()["id"]

    await sign_in(client, mailer, "eve@example.com")
    assert (await client.get("/api/cvs")).json() == []
    assert (await client.get(f"/api/cvs/{cv_id}")).status_code == 404
    patch = await client.patch(f"/api/cvs/{cv_id}", json={"name": "x"}, headers=csrf(client))
    assert patch.status_code == 404
    put = await client.put(f"/api/cvs/{cv_id}/profile", json={}, headers=csrf(client))
    assert put.status_code == 404
    assert (await client.delete(f"/api/cvs/{cv_id}", headers=csrf(client))).status_code == 404


async def test_cv_endpoints_require_login(client: AsyncClient) -> None:
    assert (await client.get("/api/cvs")).status_code == 401
    assert (await client.get("/api/preferences")).status_code == 401


async def test_preferences_roundtrip(client: AsyncClient, mailer: FakeMailer) -> None:
    await sign_in(client, mailer)
    assert (await client.get("/api/preferences")).json()["remote"] == "any"
    prefs = {
        "roles": ["Backend Developer"],
        "locations": ["Madrid"],
        "remote": "hybrid",
        "min_salary": 40000,
        "sources": ["adzuna", "greenhouse"],
    }
    resp = await client.put("/api/preferences", json=prefs, headers=csrf(client))
    assert resp.status_code == 200
    assert (await client.get("/api/preferences")).json() == prefs
    invalid = await client.put("/api/preferences", json={"remote": "moon"}, headers=csrf(client))
    assert invalid.status_code == 422

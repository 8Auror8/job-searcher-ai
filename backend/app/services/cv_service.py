"""CV versions use cases. Every query is scoped to the owner (A01 access control)."""

import uuid
from datetime import timedelta
from typing import Any

import anyio
import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import utcnow
from app.core.errors import AppError
from app.models import (
    AiUsage,
    Consent,
    ConsentKind,
    CvOrigin,
    CvVersion,
    ExtractionStatus,
    Preferences,
    User,
)
from app.schemas.cv import CvProfile, PreferencesData
from app.services.cv_extraction import (
    PROMPT_VERSION,
    AiQuotaExceeded,
    AiUnavailable,
    CvExtractor,
    ground_profile,
)
from app.services.documents import extract_text

log = structlog.get_logger()

PRIVACY_POLICY_VERSION = "2026-11"
MAX_ACTIVE_VERSIONS = 10


class CvNotFound(AppError):
    status_code, code, message = 404, "not_found", "CV not found."


class ConsentRequired(AppError):
    status_code, code = 400, "consent_required"
    message = "Consent to process your CV is required."


class TooManyVersions(AppError):
    status_code, code = 409, "too_many_versions"
    message = f"You can keep up to {MAX_ACTIVE_VERSIONS} active CV versions. Archive one first."


class NoSourceText(AppError):
    status_code, code = 409, "no_source_text"
    message = "This version has no document to analyse."


class CvService:
    def __init__(
        self, session: AsyncSession, user: User, extractor: CvExtractor | None, daily_limit: int
    ) -> None:
        self.session = session
        self.user = user
        self.extractor = extractor
        self.daily_limit = daily_limit

    # ── Queries ────────────────────────────────────────────────────────

    async def list(self, include_archived: bool = False) -> list[CvVersion]:
        stmt = select(CvVersion).where(CvVersion.user_id == self.user.id)
        if not include_archived:
            stmt = stmt.where(CvVersion.archived_at.is_(None))
        stmt = stmt.order_by(CvVersion.is_primary.desc(), CvVersion.created_at.desc())
        return list((await self.session.execute(stmt)).scalars())

    async def get(self, cv_id: uuid.UUID) -> CvVersion:
        cv = await self.session.get(CvVersion, cv_id)
        if cv is None or cv.user_id != self.user.id:
            raise CvNotFound()  # same answer for "missing" and "someone else's"
        return cv

    # ── Commands ───────────────────────────────────────────────────────

    async def create_from_file(
        self, data: bytes, name: str | None, origin: str, consent: bool
    ) -> CvVersion:
        await self._ensure_consent(consent)
        await self._ensure_capacity()
        text = await anyio.to_thread.run_sync(extract_text, data)
        default_name = "Perfil de LinkedIn" if origin == CvOrigin.LINKEDIN_PDF else "Mi CV"
        cv = CvVersion(
            user_id=self.user.id,
            name=(name or default_name)[:100],
            origin=origin,
            source_text=text,
            profile=CvProfile().model_dump(),
            extraction_status=ExtractionStatus.MANUAL,
            extraction_notes={},
        )
        self.session.add(cv)
        await self._make_primary_if_first(cv)
        await self.session.flush()
        await self._run_extraction(cv)
        await self.session.commit()
        return cv

    async def create_blank(self, name: str) -> CvVersion:
        await self._ensure_capacity()
        cv = CvVersion(
            user_id=self.user.id,
            name=name,
            origin=CvOrigin.MANUAL,
            profile=CvProfile().model_dump(),
            extraction_status=ExtractionStatus.MANUAL,
            extraction_notes={},
        )
        self.session.add(cv)
        await self._make_primary_if_first(cv)
        await self.session.commit()
        return cv

    async def reextract(self, cv_id: uuid.UUID) -> CvVersion:
        cv = await self.get(cv_id)
        if not cv.source_text:
            raise NoSourceText()
        if self.extractor is None:
            raise AiUnavailable("AI is not configured on this server.")
        await self._run_extraction(cv, raise_errors=True)
        await self.session.commit()
        return cv

    async def update(
        self,
        cv_id: uuid.UUID,
        name: str | None,
        make_primary: bool,
        archived: bool | None,
    ) -> CvVersion:
        cv = await self.get(cv_id)
        if name is not None:
            cv.name = name
        if archived is True and cv.archived_at is None:
            cv.archived_at = utcnow()
            if cv.is_primary:
                cv.is_primary = False
                await self.session.flush()
                await self._promote_latest()
        elif archived is False and cv.archived_at is not None:
            await self._ensure_capacity()
            cv.archived_at = None
        if make_primary:
            if cv.archived_at is not None:
                raise AppError("An archived version cannot be the primary one.")
            await self._set_primary(cv)
        await self.session.commit()
        return cv

    async def update_profile(self, cv_id: uuid.UUID, profile: CvProfile) -> CvVersion:
        cv = await self.get(cv_id)
        cv.profile = profile.model_dump()
        notes = dict(cv.extraction_notes or {})
        notes["edited_by_user"] = True
        cv.extraction_notes = notes
        await self.session.commit()
        return cv

    async def delete(self, cv_id: uuid.UUID) -> None:
        cv = await self.get(cv_id)
        was_primary = cv.is_primary
        await self.session.delete(cv)
        await self.session.flush()
        if was_primary:
            await self._promote_latest()
        await self.session.commit()

    # ── Preferences ────────────────────────────────────────────────────

    async def get_preferences(self) -> PreferencesData:
        prefs = await self.session.get(Preferences, self.user.id)
        return PreferencesData.model_validate(prefs.data if prefs else {})

    async def save_preferences(self, data: PreferencesData) -> PreferencesData:
        prefs = await self.session.get(Preferences, self.user.id)
        if prefs is None:
            self.session.add(Preferences(user_id=self.user.id, data=data.model_dump()))
        else:
            prefs.data = data.model_dump()
        await self.session.commit()
        return data

    # ── Helpers ────────────────────────────────────────────────────────

    async def _ensure_consent(self, consent: bool) -> None:
        existing = await self.session.scalar(
            select(Consent.id).where(
                Consent.user_id == self.user.id,
                Consent.kind == ConsentKind.CV_PROCESSING,
                Consent.revoked_at.is_(None),
            )
        )
        if existing:
            return
        if not consent:
            raise ConsentRequired()
        self.session.add(
            Consent(
                user_id=self.user.id,
                kind=ConsentKind.CV_PROCESSING,
                policy_version=PRIVACY_POLICY_VERSION,
            )
        )

    async def _ensure_capacity(self) -> None:
        active = await self.session.scalar(
            select(func.count())
            .select_from(CvVersion)
            .where(CvVersion.user_id == self.user.id, CvVersion.archived_at.is_(None))
        )
        if (active or 0) >= MAX_ACTIVE_VERSIONS:
            raise TooManyVersions()

    async def _make_primary_if_first(self, cv: CvVersion) -> None:
        has_primary = await self.session.scalar(
            select(CvVersion.id).where(
                CvVersion.user_id == self.user.id, CvVersion.is_primary.is_(True)
            )
        )
        cv.is_primary = has_primary is None

    async def _set_primary(self, cv: CvVersion) -> None:
        await self.session.execute(
            update(CvVersion)
            .where(CvVersion.user_id == self.user.id, CvVersion.id != cv.id)
            .values(is_primary=False)
        )
        cv.is_primary = True

    async def _promote_latest(self) -> None:
        latest = await self.session.scalar(
            select(CvVersion)
            .where(CvVersion.user_id == self.user.id, CvVersion.archived_at.is_(None))
            .order_by(CvVersion.created_at.desc())
            .limit(1)
        )
        if latest is not None:
            latest.is_primary = True

    async def _calls_today(self) -> int:
        since = utcnow() - timedelta(days=1)
        count = await self.session.scalar(
            select(func.count())
            .select_from(AiUsage)
            .where(AiUsage.user_id == self.user.id, AiUsage.created_at >= since)
        )
        return int(count or 0)

    async def _run_extraction(self, cv: CvVersion, raise_errors: bool = False) -> None:
        """Fill the profile with AI. Without AI (or on failure) the version stays editable."""
        if self.extractor is None or not cv.source_text:
            cv.extraction_status = ExtractionStatus.MANUAL
            cv.extraction_notes = {"reason": "ai_disabled"}
            return
        if await self._calls_today() >= self.daily_limit:
            if raise_errors:
                raise AiQuotaExceeded()
            cv.extraction_status = ExtractionStatus.FAILED
            cv.extraction_notes = {"reason": "ai_quota_exceeded"}
            return
        try:
            result = await self.extractor.extract(cv.source_text, cv.origin)
        except AiUnavailable as exc:
            self.session.add(
                AiUsage(
                    user_id=self.user.id,
                    feature="cv_extraction",
                    model=self.extractor.model,
                    success=False,
                )
            )
            if raise_errors:
                raise
            cv.extraction_status = ExtractionStatus.FAILED
            cv.extraction_notes = {"reason": exc.code}
            return

        profile, unverified = ground_profile(result.profile, cv.source_text)
        cv.profile = profile.model_dump()
        cv.extraction_status = ExtractionStatus.OK
        notes: dict[str, Any] = {
            "prompt_version": PROMPT_VERSION,
            "model": result.model,
            "unverified": unverified,
        }
        cv.extraction_notes = notes
        self.session.add(
            AiUsage(
                user_id=self.user.id,
                feature="cv_extraction",
                model=result.model,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                latency_ms=result.latency_ms,
            )
        )
        log.info(
            "cv_extracted",
            cv_id=str(cv.id),
            latency_ms=result.latency_ms,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            unverified=len(unverified),
        )

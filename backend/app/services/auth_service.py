"""Authentication use cases: registration, verification, login, sessions, password reset, Google.

Rules that matter for security (see ADR-0004 and docs/seguridad.md):
- Responses never reveal whether an email is registered.
- Opaque tokens are stored hashed; refresh tokens rotate and token reuse revokes the family.
- Resetting the password closes every session.
"""

import uuid
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import urlencode

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import Settings
from app.core.db import as_utc, utcnow
from app.core.errors import EmailNotVerified, InvalidCredentials, InvalidToken, NotAuthenticated
from app.models import OneTimeToken, RefreshToken, TokenPurpose, User
from app.repositories.users import TokenRepository, UserRepository
from app.services import mailer as mail
from app.services.google_oauth import GoogleIdentity

log = structlog.get_logger()


@dataclass(frozen=True)
class SessionTokens:
    access_token: str
    refresh_token: str
    csrf_token: str


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings, mailer: mail.Mailer) -> None:
        self.session = session
        self.settings = settings
        self.mailer = mailer
        self.users = UserRepository(session)
        self.tokens = TokenRepository(session)

    # ── Registration & email verification ──────────────────────────────

    async def register(self, email: str, password: str) -> None:
        existing = await self.users.get_by_email(email)
        if existing is None:
            user = User(email=email, password_hash=security.hash_password(password))
            self.users.add(user)
            await self.session.flush()
            await self._send_verification(user)
        elif not existing.is_verified:
            await self._send_verification(existing)
        else:
            reset = await self._create_one_time(existing, TokenPurpose.RESET_PASSWORD)
            await self.mailer.send(
                mail.account_exists_message(
                    existing.email, self._link("/login"), self._link("/reset-password", reset)
                )
            )
        await self.session.commit()

    async def resend_verification(self, email: str) -> None:
        user = await self.users.get_by_email(email)
        if user and user.is_active and not user.is_verified:
            await self._send_verification(user)
            await self.session.commit()

    async def verify_email(self, raw_token: str) -> None:
        record = await self._consume_one_time(raw_token, TokenPurpose.VERIFY_EMAIL)
        user = await self.users.get(record.user_id)
        if user is None:
            raise InvalidToken()
        user.is_verified = True
        await self.session.commit()

    # ── Login & sessions ───────────────────────────────────────────────

    async def login(
        self, email: str, password: str, user_agent: str | None
    ) -> tuple[User, SessionTokens]:
        user = await self.users.get_by_email(email)
        if user is None or user.password_hash is None:
            security.dummy_password_check()
            log.info("login_failed", reason="unknown_or_passwordless")
            raise InvalidCredentials()
        if not security.verify_password(password, user.password_hash) or not user.is_active:
            log.info("login_failed", reason="bad_password_or_inactive", user_id=str(user.id))
            raise InvalidCredentials()
        if not user.is_verified:
            raise EmailNotVerified()
        if security.password_needs_rehash(user.password_hash):
            user.password_hash = security.hash_password(password)
        user.last_login_at = utcnow()
        tokens = self._issue_session(user, user_agent)
        await self.session.commit()
        return user, tokens

    async def refresh(self, raw_refresh: str | None, user_agent: str | None) -> SessionTokens:
        if not raw_refresh:
            raise NotAuthenticated()
        record = await self.tokens.get_refresh_by_hash(security.hash_token(raw_refresh))
        if record is None:
            raise NotAuthenticated()
        now = utcnow()
        if record.revoked_at is not None:
            # A rotated token was used again: likely stolen. Kill the whole family.
            log.warning("refresh_token_reuse", user_id=str(record.user_id))
            await self.tokens.revoke_family(record.family_id, now)
            await self.session.commit()
            raise NotAuthenticated()
        user = await self.users.get(record.user_id)
        if as_utc(record.expires_at) <= now or user is None or not user.is_active:
            raise NotAuthenticated()
        record.revoked_at = now
        tokens = self._issue_session(user, user_agent, family_id=record.family_id)
        await self.session.commit()
        return tokens

    async def logout(self, raw_refresh: str | None) -> None:
        if not raw_refresh:
            return
        record = await self.tokens.get_refresh_by_hash(security.hash_token(raw_refresh))
        if record and record.revoked_at is None:
            record.revoked_at = utcnow()
            await self.session.commit()

    async def get_active_user(self, user_id: uuid.UUID) -> User:
        user = await self.users.get(user_id)
        if user is None or not user.is_active:
            raise NotAuthenticated()
        return user

    # ── Password reset ─────────────────────────────────────────────────

    async def forgot_password(self, email: str) -> None:
        user = await self.users.get_by_email(email)
        if user is None or not user.is_active:
            return
        raw = await self._create_one_time(user, TokenPurpose.RESET_PASSWORD)
        await self.mailer.send(
            mail.reset_password_message(
                user.email,
                self._link("/reset-password", raw),
                self.settings.reset_password_minutes,
            )
        )
        await self.session.commit()

    async def reset_password(self, raw_token: str, new_password: str) -> None:
        record = await self._consume_one_time(raw_token, TokenPurpose.RESET_PASSWORD)
        user = await self.users.get(record.user_id)
        if user is None or not user.is_active:
            raise InvalidToken()
        user.password_hash = security.hash_password(new_password)
        user.is_verified = True  # the user proved ownership of the email
        await self.tokens.revoke_all_for_user(user.id, utcnow())
        await self.session.commit()

    # ── Google ─────────────────────────────────────────────────────────

    async def login_with_google(
        self, identity: GoogleIdentity, user_agent: str | None
    ) -> SessionTokens:
        if not identity.email or not identity.email_verified:
            raise InvalidCredentials("Google account email is not verified.")
        user = await self.users.get_by_google_sub(identity.sub)
        if user is None:
            user = await self.users.get_by_email(identity.email)
            if user is None:
                user = User(email=identity.email, is_verified=True)
                self.users.add(user)
            elif not user.is_verified:
                # Pre-hijacking defence: someone may have registered this email with a password
                # they know. Google proves the real owner, so that unverified password is dropped.
                user.password_hash = None
            user.google_sub = identity.sub
            user.is_verified = True
            await self.session.flush()  # applies column defaults (id, is_active) to new users
        if not user.is_active:
            raise InvalidCredentials()
        user.last_login_at = utcnow()
        tokens = self._issue_session(user, user_agent)
        await self.session.commit()
        return tokens

    # ── Helpers ────────────────────────────────────────────────────────

    def _issue_session(
        self, user: User, user_agent: str | None, family_id: uuid.UUID | None = None
    ) -> SessionTokens:
        raw_refresh = security.generate_token()
        self.tokens.add_refresh(
            RefreshToken(
                user_id=user.id,
                token_hash=security.hash_token(raw_refresh),
                family_id=family_id or uuid.uuid4(),
                expires_at=utcnow() + timedelta(days=self.settings.refresh_token_days),
                user_agent=(user_agent or "")[:255] or None,
            )
        )
        return SessionTokens(
            access_token=security.create_access_token(user.id, self.settings),
            refresh_token=raw_refresh,
            csrf_token=security.generate_token(16),
        )

    async def _create_one_time(self, user: User, purpose: TokenPurpose) -> str:
        await self.tokens.delete_unused_one_time(user.id, purpose)
        lifetime = (
            timedelta(hours=self.settings.verify_email_hours)
            if purpose is TokenPurpose.VERIFY_EMAIL
            else timedelta(minutes=self.settings.reset_password_minutes)
        )
        raw = security.generate_token()
        self.tokens.add_one_time(
            OneTimeToken(
                user_id=user.id,
                purpose=purpose,
                token_hash=security.hash_token(raw),
                expires_at=utcnow() + lifetime,
            )
        )
        return raw

    async def _consume_one_time(self, raw_token: str, purpose: TokenPurpose) -> OneTimeToken:
        record = await self.tokens.get_one_time(security.hash_token(raw_token), purpose)
        if record is None or record.used_at is not None or as_utc(record.expires_at) <= utcnow():
            raise InvalidToken()
        record.used_at = utcnow()
        return record

    async def _send_verification(self, user: User) -> None:
        raw = await self._create_one_time(user, TokenPurpose.VERIFY_EMAIL)
        await self.mailer.send(
            mail.verify_email_message(
                user.email, self._link("/verify-email", raw), self.settings.verify_email_hours
            )
        )

    def _link(self, path: str, token: str | None = None) -> str:
        query = f"?{urlencode({'token': token})}" if token else ""
        return f"{self.settings.frontend_url.rstrip('/')}{path}{query}"

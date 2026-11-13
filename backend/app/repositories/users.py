"""Data access for users and their tokens. No business rules here."""

import uuid
from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OneTimeToken, RefreshToken, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        return (
            await self.session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()

    async def get_by_google_sub(self, sub: str) -> User | None:
        return (
            await self.session.execute(select(User).where(User.google_sub == sub))
        ).scalar_one_or_none()

    def add(self, user: User) -> None:
        self.session.add(user)


class TokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # Refresh tokens
    def add_refresh(self, token: RefreshToken) -> None:
        self.session.add(token)

    async def get_refresh_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_family(self, family_id: uuid.UUID, now: datetime) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    async def revoke_all_for_user(self, user_id: uuid.UUID, now: datetime) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    # One-time tokens (email verification, password reset)
    def add_one_time(self, token: OneTimeToken) -> None:
        self.session.add(token)

    async def get_one_time(self, token_hash: str, purpose: str) -> OneTimeToken | None:
        result = await self.session.execute(
            select(OneTimeToken).where(
                OneTimeToken.token_hash == token_hash, OneTimeToken.purpose == purpose
            )
        )
        return result.scalar_one_or_none()

    async def delete_unused_one_time(self, user_id: uuid.UUID, purpose: str) -> None:
        await self.session.execute(
            delete(OneTimeToken).where(
                OneTimeToken.user_id == user_id,
                OneTimeToken.purpose == purpose,
                OneTimeToken.used_at.is_(None),
            )
        )

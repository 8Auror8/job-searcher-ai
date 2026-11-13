"""FastAPI dependencies. Tests override get_session, get_mailer and get_google_client."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.core.errors import FeatureDisabled, NotAuthenticated
from app.core.middleware import ACCESS_COOKIE
from app.core.security import decode_access_token
from app.models import User
from app.services.auth_service import AuthService
from app.services.google_oauth import GoogleClient, GoogleOAuth
from app.services.mailer import ConsoleMailer, Mailer, ResendMailer

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@lru_cache
def _build_mailer(api_key: str, sender: str) -> Mailer:
    return ResendMailer(api_key, sender) if api_key else ConsoleMailer()


def get_mailer(settings: SettingsDep) -> Mailer:
    return _build_mailer(settings.resend_api_key, settings.email_from)


def get_google_client(settings: SettingsDep) -> GoogleClient:
    if not settings.google_enabled:
        raise FeatureDisabled("Google sign-in is not configured.")
    return GoogleOAuth(settings)


def get_auth_service(
    session: SessionDep, settings: SettingsDep, mailer: Annotated[Mailer, Depends(get_mailer)]
) -> AuthService:
    return AuthService(session, settings, mailer)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    request: Request, settings: SettingsDep, service: AuthServiceDep
) -> User:
    token = request.cookies.get(ACCESS_COOKIE)
    user_id = decode_access_token(token, settings) if token else None
    if user_id is None:
        raise NotAuthenticated()
    return await service.get_active_user(user_id)


CurrentUser = Annotated[User, Depends(get_current_user)]

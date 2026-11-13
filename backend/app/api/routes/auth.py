"""Authentication endpoints. Thin layer: validation in schemas, logic in AuthService."""

import secrets
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import RedirectResponse

from app.api.deps import AuthServiceDep, SettingsDep, get_google_client
from app.core.config import Settings
from app.core.errors import NotAuthenticated
from app.core.middleware import ACCESS_COOKIE, CSRF_COOKIE, REFRESH_COOKIE
from app.core.rate_limit import limiter
from app.core.security import read_state, sign_state
from app.schemas.auth import (
    EmailIn,
    LoginIn,
    MessageOut,
    RegisterIn,
    ResetPasswordIn,
    TokenIn,
    UserOut,
)
from app.services.auth_service import SessionTokens
from app.services.google_oauth import GoogleClient, GoogleOAuthError

log = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_PATH = "/api/auth"
GOOGLE_STATE_COOKIE = "g_oauth"
GOOGLE_STATE_PATH = "/api/auth/google"
ACCEPTED = MessageOut(message="If the data is valid, you will receive an email shortly.")
AUTH_LIMIT = "10/minute"


def _set_session_cookies(response: Response, tokens: SessionTokens, settings: Settings) -> None:
    common = {"secure": settings.cookie_secure, "samesite": "lax"}
    response.set_cookie(
        ACCESS_COOKIE,
        tokens.access_token,
        max_age=settings.access_token_minutes * 60,
        httponly=True,
        path="/",
        **common,  # type: ignore[arg-type]
    )
    response.set_cookie(
        REFRESH_COOKIE,
        tokens.refresh_token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        path=REFRESH_PATH,
        **common,  # type: ignore[arg-type]
    )
    response.set_cookie(
        CSRF_COOKIE,
        tokens.csrf_token,
        max_age=settings.refresh_token_days * 86400,
        httponly=False,  # the SPA must read it to send the X-CSRF-Token header
        path="/",
        **common,  # type: ignore[arg-type]
    )


def _clear_session_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_PATH)
    response.delete_cookie(CSRF_COOKIE, path="/")


@router.post("/register", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(AUTH_LIMIT)
async def register(request: Request, body: RegisterIn, service: AuthServiceDep) -> MessageOut:
    await service.register(body.email, body.password)
    return ACCEPTED


@router.post("/verify-email")
@limiter.limit(AUTH_LIMIT)
async def verify_email(request: Request, body: TokenIn, service: AuthServiceDep) -> MessageOut:
    await service.verify_email(body.token)
    return MessageOut(message="Email verified.")


@router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("3/minute")
async def resend_verification(
    request: Request, body: EmailIn, service: AuthServiceDep
) -> MessageOut:
    await service.resend_verification(body.email)
    return ACCEPTED


@router.post("/login")
@limiter.limit(AUTH_LIMIT)
async def login(
    request: Request,
    response: Response,
    body: LoginIn,
    service: AuthServiceDep,
    settings: SettingsDep,
) -> UserOut:
    user, tokens = await service.login(body.email, body.password, request.headers.get("user-agent"))
    _set_session_cookies(response, tokens, settings)
    return UserOut.model_validate(user)


@router.post("/refresh")
@limiter.limit("30/minute")
async def refresh(
    request: Request, response: Response, service: AuthServiceDep, settings: SettingsDep
) -> MessageOut:
    try:
        tokens = await service.refresh(
            request.cookies.get(REFRESH_COOKIE), request.headers.get("user-agent")
        )
    except NotAuthenticated:
        _clear_session_cookies(response)
        raise
    _set_session_cookies(response, tokens, settings)
    return MessageOut(message="Session refreshed.")


@router.post("/logout")
async def logout(request: Request, response: Response, service: AuthServiceDep) -> MessageOut:
    await service.logout(request.cookies.get(REFRESH_COOKIE))
    _clear_session_cookies(response)
    return MessageOut(message="Logged out.")


@router.post("/password/forgot", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("3/minute")
async def forgot_password(request: Request, body: EmailIn, service: AuthServiceDep) -> MessageOut:
    await service.forgot_password(body.email)
    return ACCEPTED


@router.post("/password/reset")
@limiter.limit(AUTH_LIMIT)
async def reset_password(
    request: Request, response: Response, body: ResetPasswordIn, service: AuthServiceDep
) -> MessageOut:
    await service.reset_password(body.token, body.password)
    _clear_session_cookies(response)
    return MessageOut(message="Password updated. Please sign in again.")


# ── Google ─────────────────────────────────────────────────────────────

GoogleDep = Annotated[GoogleClient, Depends(get_google_client)]


@router.get("/google/login")
@limiter.limit(AUTH_LIMIT)
async def google_login(
    request: Request, google: GoogleDep, settings: SettingsDep
) -> RedirectResponse:
    auth = google.build_authorization()
    response = RedirectResponse(auth.url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        GOOGLE_STATE_COOKIE,
        sign_state(
            {"state": auth.state, "verifier": auth.code_verifier, "nonce": auth.nonce}, settings
        ),
        max_age=600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=GOOGLE_STATE_PATH,
    )
    return response


@router.get("/google/callback")
@limiter.limit(AUTH_LIMIT)
async def google_callback(
    request: Request,
    google: GoogleDep,
    service: AuthServiceDep,
    settings: SettingsDep,
    code: Annotated[str | None, Query(max_length=2048)] = None,
    state: Annotated[str | None, Query(max_length=256)] = None,
) -> RedirectResponse:
    base = settings.frontend_url.rstrip("/")
    failure = RedirectResponse(f"{base}/login?error=google", status_code=status.HTTP_302_FOUND)
    failure.delete_cookie(GOOGLE_STATE_COOKIE, path=GOOGLE_STATE_PATH)

    saved = read_state(request.cookies.get(GOOGLE_STATE_COOKIE, ""), settings)
    if not code or not state or not saved or not secrets.compare_digest(saved["state"], state):
        log.info("google_login_failed", reason="state_mismatch")
        return failure
    try:
        identity = await google.fetch_identity(code, saved["verifier"])
        if identity.nonce != saved["nonce"]:
            raise GoogleOAuthError("nonce mismatch")
        tokens = await service.login_with_google(identity, request.headers.get("user-agent"))
    except Exception as exc:  # any failure ends in the same generic redirect
        log.info("google_login_failed", reason=type(exc).__name__)
        return failure

    success = RedirectResponse(f"{base}/app", status_code=status.HTTP_302_FOUND)
    success.delete_cookie(GOOGLE_STATE_COOKIE, path=GOOGLE_STATE_PATH)
    _set_session_cookies(success, tokens, settings)
    return success

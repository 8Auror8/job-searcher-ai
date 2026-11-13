"""Domain errors and a single JSON error format: {"error": {"code", "message"}}."""

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

log = structlog.get_logger()


class AppError(Exception):
    status_code = 400
    code = "bad_request"
    message = "Bad request."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        if message:
            self.message = message


class NotAuthenticated(AppError):
    status_code, code, message = 401, "not_authenticated", "Authentication required."


class InvalidCredentials(AppError):
    status_code, code, message = 401, "invalid_credentials", "Invalid email or password."


class EmailNotVerified(AppError):
    status_code, code, message = 403, "email_not_verified", "Email address not verified."


class InvalidToken(AppError):
    status_code, code, message = 400, "invalid_token", "Invalid or expired token."


class CsrfFailed(AppError):
    status_code, code, message = 403, "csrf_failed", "CSRF validation failed."


class FeatureDisabled(AppError):
    status_code, code, message = 404, "feature_disabled", "This feature is not enabled."


def error_body(code: str, message: str, details: Any = None) -> dict[str, Any]:
    body: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    return {"error": body}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(error_body(exc.code, exc.message), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            error_body("validation_error", "Invalid data.", details), status_code=422
        )

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limited(_: Request, __: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            error_body("rate_limited", "Too many requests. Try again later."), status_code=429
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            error_body(f"http_{exc.status_code}", str(exc.detail)), status_code=exc.status_code
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_error", path=request.url.path)
        return JSONResponse(error_body("internal_error", "Unexpected error."), status_code=500)

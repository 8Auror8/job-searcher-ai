"""Google sign-in: authorization code flow with PKCE, state and nonce (server side)."""

import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlencode

import anyio
import httpx
import jwt

from app.core.config import Settings

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105 - URL, not a secret
JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
ISSUERS = {"https://accounts.google.com", "accounts.google.com"}


@dataclass(frozen=True)
class GoogleIdentity:
    sub: str
    email: str
    email_verified: bool
    nonce: str | None


@dataclass(frozen=True)
class AuthorizationRequest:
    url: str
    state: str
    code_verifier: str
    nonce: str


class GoogleOAuthError(Exception):
    pass


class GoogleClient(Protocol):
    def build_authorization(self) -> AuthorizationRequest: ...

    async def fetch_identity(self, code: str, code_verifier: str) -> GoogleIdentity: ...


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


class GoogleOAuth:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._jwks = jwt.PyJWKClient(JWKS_URL, cache_keys=True)

    def build_authorization(self) -> AuthorizationRequest:
        state = secrets.token_urlsafe(24)
        verifier = secrets.token_urlsafe(64)
        nonce = secrets.token_urlsafe(24)
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": self.settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "code_challenge": _pkce_challenge(verifier),
            "code_challenge_method": "S256",
            "prompt": "select_account",
        }
        return AuthorizationRequest(f"{AUTH_URL}?{urlencode(params)}", state, verifier, nonce)

    async def fetch_identity(self, code: str, code_verifier: str) -> GoogleIdentity:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret,
                    "redirect_uri": self.settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                    "code_verifier": code_verifier,
                },
            )
        if resp.status_code != 200:
            raise GoogleOAuthError(f"token exchange failed ({resp.status_code})")
        id_token = resp.json().get("id_token")
        if not id_token:
            raise GoogleOAuthError("missing id_token")
        claims = await anyio.to_thread.run_sync(self._verify_id_token, id_token)
        return GoogleIdentity(
            sub=str(claims["sub"]),
            email=str(claims.get("email", "")).lower(),
            email_verified=bool(claims.get("email_verified")),
            nonce=claims.get("nonce"),
        )

    def _verify_id_token(self, id_token: str) -> dict[str, Any]:
        try:
            key = self._jwks.get_signing_key_from_jwt(id_token)
            claims: dict[str, Any] = jwt.decode(
                id_token,
                key.key,
                algorithms=["RS256"],
                audience=self.settings.google_client_id,
                options={"require": ["exp", "iat", "iss", "sub", "aud"]},
            )
        except jwt.PyJWTError as exc:
            raise GoogleOAuthError(f"invalid id_token: {exc}") from exc
        if claims.get("iss") not in ISSUERS:
            raise GoogleOAuthError("invalid issuer")
        return claims

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PASSWORD_MIN, PASSWORD_MAX = 10, 128


def _normalize_email(value: str) -> str:
    return value.strip().lower()


class EmailIn(BaseModel):
    email: EmailStr

    _norm = field_validator("email", mode="after")(_normalize_email)


class RegisterIn(EmailIn):
    password: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)
    accept_terms: bool

    @field_validator("accept_terms")
    @classmethod
    def _must_accept(cls, value: bool) -> bool:
        if not value:
            raise ValueError("You must accept the privacy policy")
        return value


class LoginIn(EmailIn):
    # No min length here: login must not reveal the password policy.
    password: str = Field(min_length=1, max_length=PASSWORD_MAX)


class TokenIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class ResetPasswordIn(TokenIn):
    password: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    is_verified: bool
    has_password: bool
    google_linked: bool
    created_at: datetime


class MessageOut(BaseModel):
    message: str

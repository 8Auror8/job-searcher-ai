"""Outgoing email. Resend in production; logs in development; captured in tests."""

from dataclasses import dataclass
from html import escape
from typing import Protocol

import httpx
import structlog

log = structlog.get_logger()


@dataclass(frozen=True)
class Email:
    to: str
    subject: str
    text: str
    html: str


class Mailer(Protocol):
    async def send(self, email: Email) -> None: ...


class ConsoleMailer:
    """Development only: prints the email (including links) to the API logs."""

    async def send(self, email: Email) -> None:
        log.info("email_dev_output", to=email.to, subject=email.subject, text=email.text)


class ResendMailer:
    def __init__(self, api_key: str, sender: str) -> None:
        self.api_key = api_key
        self.sender = sender

    async def send(self, email: Email) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "from": self.sender,
                    "to": [email.to],
                    "subject": email.subject,
                    "text": email.text,
                    "html": email.html,
                },
            )
        if resp.status_code >= 400:
            log.error("email_send_failed", status=resp.status_code)
            resp.raise_for_status()


def _build(to: str, subject: str, intro: str, link: str, cta: str, outro: str) -> Email:
    text = f"{intro}\n\n{cta}: {link}\n\n{outro}\n\n— JobPilot AI"
    html = (
        f"<p>{escape(intro)}</p>"
        f'<p><a href="{escape(link)}">{escape(cta)}</a></p>'
        f"<p style='color:#666'>{escape(outro)}</p><p>— JobPilot AI</p>"
    )
    return Email(to=to, subject=subject, text=text, html=html)


def verify_email_message(to: str, link: str, hours: int) -> Email:
    return _build(
        to,
        "Confirma tu email en JobPilot AI",
        "Gracias por registrarte en JobPilot AI. Confirma tu dirección de email para empezar.",
        link,
        "Confirmar email",
        f"El enlace caduca en {hours} horas. Si no creaste esta cuenta, ignora este mensaje.",
    )


def account_exists_message(to: str, login_link: str, reset_link: str) -> Email:
    return _build(
        to,
        "Intento de registro en JobPilot AI",
        "Alguien ha intentado crear una cuenta con tu email, pero ya tienes una. "
        f"Si has olvidado tu contraseña, puedes restablecerla aquí: {reset_link}",
        login_link,
        "Iniciar sesión",
        "Si no fuiste tú, puedes ignorar este mensaje.",
    )


def reset_password_message(to: str, link: str, minutes: int) -> Email:
    return _build(
        to,
        "Restablece tu contraseña de JobPilot AI",
        "Hemos recibido una solicitud para restablecer tu contraseña.",
        link,
        "Restablecer contraseña",
        f"El enlace caduca en {minutes} minutos. Si no lo pediste, ignora este mensaje.",
    )

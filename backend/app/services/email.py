"""Small SMTP adapter; in development, links print to the backend terminal."""
import smtplib
from email.message import EmailMessage

from app.config import settings


def send_auth_link(email: str, purpose: str, token: str) -> None:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/auth/{purpose}?token={token}"
    subject = "Reset your password"
    body = f"Use this one-time link within the allowed time:\n\n{url}\n"
    if not settings.SMTP_HOST:
        # Local-only convenience. Configure SMTP before using outside development.
        if settings.APP_ENV != "development":
            raise RuntimeError("SMTP_HOST must be configured outside development")
        print(f"[DEV AUTH EMAIL] to={email} subject={subject}\n{body}")
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
        smtp.send_message(message)

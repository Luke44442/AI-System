"""Transactional email sending.

Uses SMTP when configured; otherwise logs the message (dev-friendly, never crashes
a request because email is down). Call sites use the high-level helpers.
"""
from __future__ import annotations
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, html_body: str, text_body: str | None = None) -> bool:
    """Send an email. Returns True if sent via SMTP, False if logged-only/failed."""
    if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD):
        logger.info("EMAIL (not sent — SMTP unconfigured) to=%s subject=%s\n%s", to, subject, text_body or html_body)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAILS_FROM_EMAIL
    msg["To"] = to
    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, [to], msg.as_string())
        logger.info("email_sent to=%s subject=%s", to, subject)
        return True
    except Exception as exc:  # pragma: no cover - network/SMTP failures
        logger.error("email_send_failed to=%s error=%s", to, exc)
        return False


def send_password_reset_email(to: str, reset_url: str) -> bool:
    subject = "Reset your Aurevia password"
    html = f"""
    <div style="font-family:Georgia,serif;max-width:480px;margin:auto;color:#0A0A0A">
      <h2 style="font-weight:normal">Reset your password</h2>
      <p>We received a request to reset your Aurevia password. This link expires in 1 hour.</p>
      <p><a href="{reset_url}" style="background:#C9A84C;color:#fff;padding:12px 24px;
         text-decoration:none;border-radius:4px;display:inline-block">Reset Password</a></p>
      <p style="color:#666;font-size:13px">If you didn't request this, you can safely ignore this email.</p>
    </div>"""
    text = f"Reset your Aurevia password (expires in 1 hour): {reset_url}"
    return send_email(to, subject, html, text)


def send_welcome_email(to: str, first_name: str | None = None) -> bool:
    name = first_name or "there"
    subject = "Welcome to Aurevia"
    html = f"""
    <div style="font-family:Georgia,serif;max-width:480px;margin:auto;color:#0A0A0A">
      <h2 style="font-weight:normal">Welcome, {name}</h2>
      <p>You've joined Aurevia — luxury fragrances, sneakers, streetwear, and more,
         each piece verified for authenticity.</p>
      <p><a href="https://aurevia.com/products" style="background:#C9A84C;color:#fff;padding:12px 24px;
         text-decoration:none;border-radius:4px;display:inline-block">Start Shopping</a></p>
    </div>"""
    text = f"Welcome to Aurevia, {name}. Start shopping: https://aurevia.com/products"
    return send_email(to, subject, html, text)

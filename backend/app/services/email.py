"""
Email service — uses SMTP (configure via env vars).
In development, emails are logged to stdout instead of sent.
Set EMAIL_ENABLED=true + SMTP_* vars in .env to enable real sending.
"""
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, html: str, text: Optional[str] = None):
    if not getattr(settings, "email_enabled", False):
        logger.info(f"[EMAIL] To: {to} | Subject: {subject}")
        logger.debug(f"[EMAIL] Body: {text or html[:200]}")
        return

    import asyncio
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to
    if text:
        msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    def _send():
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_tls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

    try:
        await asyncio.to_thread(_send)
    except Exception:
        # Delivery failure must never crash the request that triggered it
        # (module completion, cert award, etc.) or roll back its transaction.
        logger.exception(f"[EMAIL] Failed to send to {to!r}: {subject!r}")


async def send_welcome_email(to: str, name: str):
    await send_email(to, f"Welcome to Sedna Academy, {name.split()[0]}!", f"""
    <h2>Welcome to Sedna Academy</h2>
    <p>Hi {name.split()[0]},</p>
    <p>Your account is ready. Start your first learning path and earn your first certificate.</p>
    <p><a href="{getattr(settings, 'app_url', 'http://localhost:5173')}/paths">Browse learning paths →</a></p>
    """)


async def send_cert_email(to: str, name: str, cert_name: str, credential: str):
    await send_email(to, f"Certificate earned: {cert_name}", f"""
    <h2>Congratulations, {name.split()[0]}! 🎉</h2>
    <p>You've earned your <strong>{cert_name}</strong> certificate.</p>
    <p>Credential number: <code>{credential}</code></p>
    <p><a href="{getattr(settings, 'app_url', 'http://localhost:5173')}/certs">View your certificate →</a></p>
    """)


async def send_near_cert_email(to: str, name: str, cert_name: str, modules_left: int):
    await send_email(to, f"You're {modules_left} module{'s' if modules_left > 1 else ''} from your certificate", f"""
    <h2>Almost there, {name.split()[0]}!</h2>
    <p>Complete <strong>{modules_left} more module{'s' if modules_left > 1 else ''}</strong> to earn <strong>{cert_name}</strong>.</p>
    <p><a href="{getattr(settings, 'app_url', 'http://localhost:5173')}/paths">Continue learning →</a></p>
    """)


async def send_invite_email(to: str, name: str, inviter_name: str, org_name: str = "your team"):
    await send_email(to, f"{inviter_name} invited you to Sedna Academy", f"""
    <h2>You've been invited to Sedna Academy</h2>
    <p>Hi {name.split()[0]},</p>
    <p><strong>{inviter_name}</strong> has invited you to join {org_name} on Sedna Academy.</p>
    <p><a href="{getattr(settings, 'app_url', 'http://localhost:5173')}/login">Sign in to get started →</a></p>
    """)


async def send_streak_reminder(to: str, name: str, streak_days: int):
    await send_email(to, f"Don't lose your {streak_days}-day streak!", f"""
    <h2>Keep your streak alive, {name.split()[0]}! 🔥</h2>
    <p>You're on a <strong>{streak_days}-day learning streak</strong>. Log in today to keep it going.</p>
    <p><a href="{getattr(settings, 'app_url', 'http://localhost:5173')}">Continue learning →</a></p>
    """)

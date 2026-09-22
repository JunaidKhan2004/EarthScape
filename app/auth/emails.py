import logging

from flask import render_template, current_app
from flask_mail import Message

from app import mail

logger = logging.getLogger("auth.emails")


def send_password_reset_email(to_email: str, name: str, reset_url: str) -> bool:
    """Sends the password-reset email. Returns True if sent, False if mail
    isn't configured (logs the link instead so the flow still works in dev)."""
    if not current_app.config.get("MAIL_USERNAME"):
        logger.warning(
            "MAIL_USERNAME not configured -- skipping real email send. "
            "Password reset link for %s: %s",
            to_email,
            reset_url,
        )
        return False

    html_body = render_template(
        "emails/password_reset.html", name=name, reset_url=reset_url
    )
    text_body = (
        f"Hi {name},\n\n"
        "We received a request to reset your EarthScape Climate Agency password.\n"
        f"Reset it here: {reset_url}\n\n"
        "This link expires in 1 hour. If you didn't request this, you can ignore this email."
    )

    msg = Message(
        subject="Reset your EarthScape password",
        recipients=[to_email],
        body=text_body,
        html=html_body,
    )

    try:
        mail.send(msg)
        return True
    except Exception:
        logger.exception(
            "Failed to send password reset email to %s -- check GMAIL_USER/GMAIL_APP_PASSWORD. "
            "Reset link: %s",
            to_email,
            reset_url,
        )
        return False

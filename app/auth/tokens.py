"""
Password-reset tokens: signed, time-limited, and stateless (no DB row to
clean up). itsdangerous signs the user's email with the app's SECRET_KEY,
so a token can't be forged or reused past its expiry, but nothing needs to
be stored or invalidated server-side.
"""
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app

RESET_SALT = "password-reset"


def generate_reset_token(email: str) -> str:
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email.lower(), salt=RESET_SALT)


def verify_reset_token(token: str) -> str | None:
    """Returns the email the token was issued for, or None if invalid/expired."""
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    max_age = current_app.config["RESET_TOKEN_MAX_AGE_SECONDS"]
    try:
        return serializer.loads(token, salt=RESET_SALT, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None

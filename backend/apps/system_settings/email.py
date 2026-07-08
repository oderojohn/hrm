"""Builds a live SMTP connection from the admin-configured EmailSettings row,
so notification emails (leave approvals, attendance corrections, etc.) go out
through whatever the Settings UI has configured (e.g. Gmail) instead of only
the static EMAIL_BACKEND in config/settings.py.
"""
from django.conf import settings
from django.core.mail import get_connection


def get_configured_connection():
    """Returns a ready-to-use SMTP connection, or None if EmailSettings isn't
    fully configured yet — callers should fall back to send_mail's default
    backend (the console backend in dev) when this returns None.
    """
    from apps.system_settings.models import EmailSettings

    email_settings = EmailSettings.get_solo()
    if not (email_settings.smtp_host and email_settings.smtp_username and email_settings.smtp_password):
        return None

    return get_connection(
        backend="django.core.mail.backends.smtp.EmailBackend",
        host=email_settings.smtp_host,
        port=email_settings.smtp_port or 587,
        username=email_settings.smtp_username,
        password=email_settings.smtp_password,
        use_tls=email_settings.use_tls,
    )


def get_from_email():
    from apps.system_settings.models import EmailSettings

    email_settings = EmailSettings.get_solo()
    return email_settings.from_email or email_settings.smtp_username or settings.DEFAULT_FROM_EMAIL

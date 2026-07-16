from django.db import models

from apps.core.models import BaseModel


class SystemSetting(BaseModel):
    """Generic key/value store for misc toggles (session timeout override, theme default, etc.)."""

    key = models.CharField(max_length=150, unique=True)
    value = models.TextField(blank=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return self.key


class EmailSettings(BaseModel):
    """Effectively a singleton — SMTP config editable from the Settings UI.

    When smtp_host/smtp_username/smtp_password are all set, apps.system_settings.email
    builds a live SMTP connection from these values for every outgoing notification
    email; otherwise sending falls back to the static EMAIL_BACKEND in
    config/settings.py (console backend by default in dev).
    """

    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.PositiveIntegerField(null=True, blank=True, default=587)
    smtp_username = models.CharField(max_length=255, blank=True)
    smtp_password = models.CharField(max_length=255, blank=True)
    use_tls = models.BooleanField(default=True)
    from_email = models.EmailField(blank=True)

    class Meta:
        verbose_name = "Email Settings"
        verbose_name_plural = "Email Settings"

    def __str__(self):
        return f"Email Settings ({self.smtp_host or 'not configured'})"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class WeeklyReportSettings(BaseModel):
    """Effectively a singleton — controls the Monday-morning scheduled
    weekly report email (apps.reports.views.WeeklySummaryCronView). The
    schedule itself (every Monday 08:00 EAT) is fixed in backend/vercel.json
    since Vercel Cron requires a redeploy to change it; this only controls
    whether it fires and who beyond HR Managers/Super Admins gets it.
    """

    is_enabled = models.BooleanField(default=True)
    extra_recipients = models.JSONField(
        default=list,
        blank=True,
        help_text="Additional email addresses to include, beyond every active HR Manager/Super Admin.",
    )

    class Meta:
        verbose_name = "Weekly Report Settings"
        verbose_name_plural = "Weekly Report Settings"

    def __str__(self):
        return "Weekly Report Settings"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"is_enabled": True, "extra_recipients": []})
        return obj


class SMSGatewaySettings(BaseModel):
    """Effectively a singleton — documents the SMS gateway config for review in the admin UI.

    Actual SMS sending is driven by SMS_BACKEND settings in config/settings.py.
    """

    provider_name = models.CharField(max_length=100, blank=True)
    sender_id = models.CharField(max_length=50, blank=True)
    is_enabled = models.BooleanField(default=False)

    class Meta:
        verbose_name = "SMS Gateway Settings"
        verbose_name_plural = "SMS Gateway Settings"

    def __str__(self):
        return f"SMS Gateway Settings ({self.provider_name or 'not configured'})"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class BackupRecord(BaseModel):
    """Logs that a backup event happened. Does not perform any real backup/restore logic."""

    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    triggered_by = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    file_name = models.CharField(max_length=255, blank=True)
    size_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IN_PROGRESS
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.file_name or 'backup'} ({self.status})"

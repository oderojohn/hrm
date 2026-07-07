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
    """Effectively a singleton — documents the SMTP config for review in the admin UI.

    Actual email sending is driven by EMAIL_BACKEND settings in config/settings.py.
    """

    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.PositiveIntegerField(null=True, blank=True)
    smtp_username = models.CharField(max_length=255, blank=True)
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

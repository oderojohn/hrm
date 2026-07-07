from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class BaseModel(TimeStampedModel):
    """Standard base for domain models: timestamps + soft delete."""

    is_deleted = models.BooleanField(default=False)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.save(update_fields=["is_deleted", "updated_at"])


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        APPROVE = "APPROVE", "Approve"
        REJECT = "REJECT", "Reject"
        CANCEL = "CANCEL", "Cancel"
        EXPORT = "EXPORT", "Export"
        OTHER = "OTHER", "Other"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=64, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["model_name", "object_id"]),
            models.Index(fields=["-timestamp"]),
        ]

    def __str__(self):
        return f"{self.action} {self.model_name}#{self.object_id} by {self.actor}"


class LoginHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="login_history"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    success = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user} @ {self.timestamp} ({'ok' if self.success else 'failed'})"


class CompanyProfile(models.Model):
    """Effectively a singleton — one row holds the active company profile."""

    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to="company/", null=True, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    kra_pin = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="Kenya")
    website = models.URLField(blank=True)
    time_zone = models.CharField(max_length=64, default="Africa/Nairobi")
    date_format = models.CharField(max_length=32, default="DD/MM/YYYY")
    established_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company Profile"
        verbose_name_plural = "Company Profile"

    def __str__(self):
        return self.name

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"name": "Nexas Systems"})
        return obj


class PublicHoliday(BaseModel):
    name = models.CharField(max_length=150)
    date = models.DateField()
    is_recurring_annually = models.BooleanField(default=False)
    description = models.CharField(max_length=255, blank=True)
    branch = models.ForeignKey(
        "organization.Branch",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="holidays",
        help_text="Leave blank for a company-wide holiday.",
    )

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.name} ({self.date})"

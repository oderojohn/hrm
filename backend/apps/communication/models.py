from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Announcement(BaseModel):
    class Audience(models.TextChoices):
        ALL = "ALL", "All Employees"
        DEPARTMENT = "DEPARTMENT", "Department"
        BRANCH = "BRANCH", "Branch"

    title = models.CharField(max_length=255)
    body = models.TextField()
    audience = models.CharField(
        max_length=20, choices=Audience.choices, default=Audience.ALL
    )
    department = models.ForeignKey(
        "organization.Department",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="announcements",
    )
    branch = models.ForeignKey(
        "organization.Branch",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="announcements",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Notification(BaseModel):
    class Channel(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"
        IN_APP = "IN_APP", "In-App"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    channel = models.CharField(
        max_length=10, choices=Channel.choices, default=Channel.IN_APP
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    related_url = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} -> {self.recipient}"

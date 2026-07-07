from django.db import models

from apps.core.models import BaseModel


class DisciplinaryCase(BaseModel):
    class CaseType(models.TextChoices):
        WARNING = "WARNING", "Warning"
        SHOW_CAUSE = "SHOW_CAUSE", "Show Cause"
        SUSPENSION = "SUSPENSION", "Suspension"
        HEARING = "HEARING", "Hearing"
        TERMINATION = "TERMINATION", "Termination"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="disciplinary_cases",
    )
    case_type = models.CharField(max_length=20, choices=CaseType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField()
    raised_by = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    incident_date = models.DateField()
    resolution = models.TextField(blank=True)
    resolved_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-incident_date"]

    def __str__(self):
        return f"{self.title} - {self.employee}"


class DisciplinaryAction(BaseModel):
    class ActionType(models.TextChoices):
        WARNING_LETTER = "WARNING_LETTER", "Warning Letter"
        SHOW_CAUSE_LETTER = "SHOW_CAUSE_LETTER", "Show Cause Letter"
        SUSPENSION = "SUSPENSION", "Suspension"
        TERMINATION = "TERMINATION", "Termination"
        OTHER = "OTHER", "Other"

    case = models.ForeignKey(
        DisciplinaryCase, on_delete=models.CASCADE, related_name="actions"
    )
    action_type = models.CharField(max_length=20, choices=ActionType.choices)
    issued_date = models.DateField()
    issued_by = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    document = models.FileField(
        upload_to="disciplinary/documents/", null=True, blank=True
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-issued_date"]

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.case}"


class Hearing(BaseModel):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    case = models.ForeignKey(
        DisciplinaryCase, on_delete=models.CASCADE, related_name="hearings"
    )
    scheduled_date = models.DateTimeField()
    panel_members = models.ManyToManyField(
        "employees.Employee", blank=True, related_name="+"
    )
    outcome = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)

    class Meta:
        ordering = ["-scheduled_date"]

    def __str__(self):
        return f"Hearing for {self.case} @ {self.scheduled_date}"

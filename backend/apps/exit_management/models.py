from django.db import models

from apps.core.models import BaseModel


class ExitProcess(BaseModel):
    class ExitType(models.TextChoices):
        RESIGNATION = "RESIGNATION", "Resignation"
        TERMINATION = "TERMINATION", "Termination"
        RETIREMENT = "RETIREMENT", "Retirement"
        CONTRACT_END = "CONTRACT_END", "Contract End"

    class Status(models.TextChoices):
        INITIATED = "INITIATED", "Initiated"
        CLEARANCE_IN_PROGRESS = "CLEARANCE_IN_PROGRESS", "Clearance In Progress"
        COMPLETED = "COMPLETED", "Completed"

    employee = models.OneToOneField(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="exit_process",
    )
    exit_type = models.CharField(max_length=20, choices=ExitType.choices)
    resignation_date = models.DateField(null=True, blank=True)
    last_working_date = models.DateField(null=True, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=25, choices=Status.choices, default=Status.INITIATED
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_exit_type_display()}"


class ClearanceItem(BaseModel):
    exit_process = models.ForeignKey(
        ExitProcess,
        on_delete=models.CASCADE,
        related_name="clearance_items",
    )
    department = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    is_cleared = models.BooleanField(default=False)
    cleared_by = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    cleared_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["department", "description"]

    def __str__(self):
        return f"{self.exit_process.employee.full_name} - {self.department}: {self.description}"


class ExitInterview(BaseModel):
    exit_process = models.OneToOneField(
        ExitProcess,
        on_delete=models.CASCADE,
        related_name="exit_interview",
    )
    conducted_by = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    interview_date = models.DateField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    reason_for_leaving = models.TextField(blank=True)
    would_recommend_company = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ["-interview_date"]

    def __str__(self):
        return f"Exit Interview - {self.exit_process.employee.full_name}"

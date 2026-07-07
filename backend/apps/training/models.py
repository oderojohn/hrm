from django.db import models

from apps.core.models import BaseModel


class TrainingProgram(BaseModel):
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    provider = models.CharField(max_length=200, blank=True)
    duration_hours = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} ({self.code})"


class TrainingSession(BaseModel):
    program = models.ForeignKey(
        "training.TrainingProgram", on_delete=models.CASCADE, related_name="sessions"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.CharField(max_length=200, blank=True)
    trainer = models.CharField(max_length=200, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.program.title} - {self.start_date}"


class TrainingAttendance(BaseModel):
    class Status(models.TextChoices):
        ENROLLED = "ENROLLED", "Enrolled"
        ATTENDED = "ATTENDED", "Attended"
        ABSENT = "ABSENT", "Absent"
        COMPLETED = "COMPLETED", "Completed"

    session = models.ForeignKey(
        "training.TrainingSession", on_delete=models.CASCADE, related_name="attendances"
    )
    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="training_records"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ENROLLED
    )
    certificate = models.FileField(
        upload_to="training/certificates/", null=True, blank=True
    )
    completion_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.session}"

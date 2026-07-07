from django.db import models

from apps.core.models import BaseModel


class Goal(BaseModel):
    class Status(models.TextChoices):
        NOT_STARTED = "NOT_STARTED", "Not Started"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        MISSED = "MISSED", "Missed"

    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="goals"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOT_STARTED
    )
    weight_percentage = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.employee})"


class KPI(BaseModel):
    goal = models.ForeignKey(
        Goal, null=True, blank=True, on_delete=models.CASCADE, related_name="kpis"
    )
    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="kpis"
    )
    name = models.CharField(max_length=255)
    target_value = models.CharField(max_length=100)
    actual_value = models.CharField(max_length=100, blank=True)
    measurement_unit = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.employee}"


class PerformanceReview(BaseModel):
    class ReviewType(models.TextChoices):
        QUARTERLY = "QUARTERLY", "Quarterly"
        ANNUAL = "ANNUAL", "Annual"
        PROBATION = "PROBATION", "Probation"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"

    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="performance_reviews"
    )
    reviewer = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviews_conducted",
    )
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    review_type = models.CharField(
        max_length=20, choices=ReviewType.choices, default=ReviewType.QUARTERLY
    )
    overall_rating = models.PositiveIntegerField(null=True, blank=True)
    manager_comments = models.TextField(blank=True)
    employee_feedback = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["-review_period_end"]

    def __str__(self):
        return f"{self.employee} review ({self.review_period_start} - {self.review_period_end})"


class PromotionRecommendation(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="promotion_recommendations"
    )
    recommended_by = models.ForeignKey(
        "employees.Employee", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    current_position = models.ForeignKey(
        "organization.Position",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    recommended_position = models.ForeignKey(
        "organization.Position",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    justification = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Promotion for {self.employee} ({self.status})"

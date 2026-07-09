from django.db import models

from apps.core.models import BaseModel


class Branch(BaseModel):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    manager = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="managed_branches",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(BaseModel):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="departments"
    )
    head = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="headed_departments",
    )
    parent_department = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sub_departments",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Position(BaseModel):
    title = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="positions"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class WorkShift(BaseModel):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration_minutes = models.PositiveIntegerField(default=60)
    grace_period_minutes = models.PositiveIntegerField(
        default=10, help_text="Minutes of tolerance before a clock-in counts as late."
    )
    working_days = models.JSONField(
        default=list,
        help_text="List of ISO weekday numbers this shift is active on, e.g. [1,2,3,4,5] for Mon-Fri.",
    )
    is_flexible = models.BooleanField(
        default=False,
        help_text="No fixed hours — clock-ins/outs are never marked late or an early "
        "departure, and no overtime is computed. start_time/end_time are ignored for "
        "attendance evaluation (kept only for display) when this is on.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

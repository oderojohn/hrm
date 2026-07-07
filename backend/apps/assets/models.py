from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class Asset(BaseModel):
    class Category(models.TextChoices):
        LAPTOP = "LAPTOP", "Laptop"
        DESKTOP = "DESKTOP", "Desktop"
        MOBILE_PHONE = "MOBILE_PHONE", "Mobile Phone"
        VEHICLE = "VEHICLE", "Vehicle"
        ACCESS_CARD = "ACCESS_CARD", "Access Card"
        MONITOR = "MONITOR", "Monitor"
        PRINTER = "PRINTER", "Printer"
        OTHER = "OTHER", "Other"

    class Condition(models.TextChoices):
        NEW = "NEW", "New"
        GOOD = "GOOD", "Good"
        FAIR = "FAIR", "Fair"
        POOR = "POOR", "Poor"
        DAMAGED = "DAMAGED", "Damaged"

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_MAINTENANCE = "IN_MAINTENANCE", "In Maintenance"
        RETIRED = "RETIRED", "Retired"
        LOST = "LOST", "Lost"

    asset_tag = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=Category.choices)
    serial_number = models.CharField(max_length=100, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    condition = models.CharField(
        max_length=10, choices=Condition.choices, default=Condition.GOOD
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE
    )
    branch = models.ForeignKey(
        "organization.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assets",
    )

    class Meta:
        ordering = ["asset_tag"]

    def __str__(self):
        return f"{self.asset_tag} - {self.name}"


class AssetAssignment(BaseModel):
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="assignments"
    )
    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="asset_assignments"
    )
    assigned_date = models.DateField(default=timezone.now)
    returned_at = models.DateField(null=True, blank=True)
    condition_on_assign = models.CharField(max_length=10, blank=True)
    condition_on_return = models.CharField(max_length=10, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-assigned_date"]

    def __str__(self):
        return f"{self.asset.asset_tag} -> {self.employee.full_name}"


class AssetMaintenanceRecord(BaseModel):
    class Status(models.TextChoices):
        REPORTED = "REPORTED", "Reported"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"

    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="maintenance_records"
    )
    reported_date = models.DateField()
    description = models.TextField()
    resolved_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.REPORTED
    )

    class Meta:
        ordering = ["-reported_date"]

    def __str__(self):
        return f"Maintenance for {self.asset.asset_tag} ({self.reported_date})"


class LostAssetReport(BaseModel):
    class Status(models.TextChoices):
        REPORTED = "REPORTED", "Reported"
        INVESTIGATING = "INVESTIGATING", "Investigating"
        RESOLVED = "RESOLVED", "Resolved"
        WRITTEN_OFF = "WRITTEN_OFF", "Written Off"

    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="loss_reports"
    )
    employee = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lost_asset_reports",
    )
    reported_date = models.DateField()
    circumstances = models.TextField()
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.REPORTED
    )

    class Meta:
        ordering = ["-reported_date"]

    def __str__(self):
        return f"Loss report for {self.asset.asset_tag} ({self.reported_date})"

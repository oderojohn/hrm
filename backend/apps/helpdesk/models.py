from django.db import models

from apps.core.models import BaseModel


class Ticket(BaseModel):
    class Category(models.TextChoices):
        HR = "HR", "HR"
        IT = "IT", "IT"
        FACILITIES = "FACILITIES", "Facilities"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    category = models.CharField(max_length=20, choices=Category.choices)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    raised_by = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="tickets_raised"
    )
    assigned_to = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tickets_assigned",
    )
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.category}] {self.subject}"

    @property
    def response_time_hours(self):
        if self.resolved_at:
            return round((self.resolved_at - self.created_at).total_seconds() / 3600, 1)
        return None


class TicketComment(BaseModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey("employees.Employee", on_delete=models.CASCADE)
    comment = models.TextField()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.ticket}"


class TicketAttachment(BaseModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="helpdesk/attachments/")
    uploaded_by = models.ForeignKey(
        "employees.Employee", null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Attachment for {self.ticket}"

from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class JobVacancy(BaseModel):
    class EmploymentType(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full Time"
        PART_TIME = "PART_TIME", "Part Time"
        CONTRACT = "CONTRACT", "Contract"
        INTERNSHIP = "INTERNSHIP", "Internship"
        CASUAL = "CASUAL", "Casual"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"
        ON_HOLD = "ON_HOLD", "On Hold"

    title = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(
        "organization.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="vacancies",
    )
    branch = models.ForeignKey(
        "organization.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="vacancies",
    )
    employment_type = models.CharField(
        max_length=20, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME
    )
    description = models.TextField()
    requirements = models.TextField(blank=True)
    number_of_positions = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    posted_date = models.DateField(default=timezone.now)
    closing_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-posted_date"]

    def __str__(self):
        return f"{self.title} ({self.code})"


class Candidate(BaseModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    resume = models.FileField(upload_to="recruitment/resumes/", null=True, blank=True)
    cover_letter = models.FileField(upload_to="recruitment/cover_letters/", null=True, blank=True)
    source = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class Application(BaseModel):
    class Status(models.TextChoices):
        APPLIED = "APPLIED", "Applied"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        INTERVIEWING = "INTERVIEWING", "Interviewing"
        OFFERED = "OFFERED", "Offered"
        HIRED = "HIRED", "Hired"
        REJECTED = "REJECTED", "Rejected"

    vacancy = models.ForeignKey(
        JobVacancy, on_delete=models.CASCADE, related_name="applications"
    )
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name="applications"
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.candidate.full_name} -> {self.vacancy.title}"


class Interview(BaseModel):
    class Mode(models.TextChoices):
        IN_PERSON = "IN_PERSON", "In Person"
        PHONE = "PHONE", "Phone"
        VIDEO = "VIDEO", "Video"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="interviews"
    )
    scheduled_at = models.DateTimeField()
    interviewer = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="interviews_conducted",
    )
    location = models.CharField(max_length=255, blank=True)
    mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.IN_PERSON)
    feedback = models.TextField(blank=True)
    rating = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)

    class Meta:
        ordering = ["-scheduled_at"]

    def __str__(self):
        return f"Interview: {self.application} @ {self.scheduled_at}"


class OfferLetter(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent"
        ACCEPTED = "ACCEPTED", "Accepted"
        DECLINED = "DECLINED", "Declined"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    application = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="offer_letter"
    )
    position_title = models.CharField(max_length=150)
    proposed_start_date = models.DateField()
    document = models.FileField(upload_to="recruitment/offers/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    sent_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Offer for {self.application.candidate.full_name} ({self.status})"

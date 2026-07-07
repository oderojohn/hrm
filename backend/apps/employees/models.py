from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


def generate_employee_number():
    year = timezone.now().year
    prefix = f"NX{year}"
    last = (
        Employee.all_objects.filter(employee_number__startswith=prefix)
        .order_by("-employee_number")
        .first()
    )
    if last and last.employee_number[len(prefix):].isdigit():
        seq = int(last.employee_number[len(prefix):]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


class Employee(BaseModel):
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    class MaritalStatus(models.TextChoices):
        SINGLE = "SINGLE", "Single"
        MARRIED = "MARRIED", "Married"
        DIVORCED = "DIVORCED", "Divorced"
        WIDOWED = "WIDOWED", "Widowed"

    class EmploymentType(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full-Time"
        PART_TIME = "PART_TIME", "Part-Time"
        CONTRACT = "CONTRACT", "Contract"
        INTERNSHIP = "INTERNSHIP", "Internship"
        CASUAL = "CASUAL", "Casual"

    class EmploymentStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        RESIGNED = "RESIGNED", "Resigned"
        TERMINATED = "TERMINATED", "Terminated"
        RETIRED = "RETIRED", "Retired"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employee",
    )
    employee_number = models.CharField(max_length=20, unique=True, blank=True)
    device_user_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="User ID as enrolled on the biometric attendance device (e.g. ZKTeco), used to match clock-in/out events.",
    )
    photo = models.ImageField(upload_to="employees/photos/", null=True, blank=True)

    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    national_id = models.CharField(max_length=30, unique=True, null=True, blank=True)
    passport_number = models.CharField(max_length=30, blank=True)
    kra_pin = models.CharField(max_length=30, blank=True)
    nssf_number = models.CharField(max_length=30, blank=True)
    shif_number = models.CharField(max_length=30, blank=True, verbose_name="SHIF/NHIF Number")
    bank_name = models.CharField(max_length=100, blank=True)
    bank_branch = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)

    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    alternative_phone = models.CharField(max_length=30, blank=True)

    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)

    nationality = models.CharField(max_length=100, default="Kenyan")
    marital_status = models.CharField(max_length=10, choices=MaritalStatus.choices, blank=True)
    address = models.CharField(max_length=255, blank=True)
    county = models.CharField(max_length=100, blank=True)
    sub_county = models.CharField(max_length=100, blank=True)
    postal_address = models.CharField(max_length=100, blank=True)

    employment_date = models.DateField()
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    department = models.ForeignKey(
        "organization.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employees",
    )
    position = models.ForeignKey(
        "organization.Position",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employees",
    )
    branch = models.ForeignKey(
        "organization.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employees",
    )
    reporting_manager = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="direct_reports",
    )
    probation_end_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    work_shift = models.ForeignKey(
        "organization.WorkShift",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employees",
    )
    employment_status = models.CharField(
        max_length=20, choices=EmploymentStatus.choices, default=EmploymentStatus.ACTIVE
    )

    class Meta:
        ordering = ["employee_number"]

    def __str__(self):
        return f"{self.employee_number} - {self.full_name}"

    def save(self, *args, **kwargs):
        if not self.employee_number:
            self.employee_number = generate_employee_number()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(p for p in parts if p)


class Education(BaseModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="education")
    institution = models.CharField(max_length=200)
    qualification = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    grade = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["-end_date"]

    def __str__(self):
        return f"{self.qualification} - {self.institution}"


class Certification(BaseModel):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="certifications"
    )
    name = models.CharField(max_length=200)
    issuing_body = models.CharField(max_length=200, blank=True)
    credential_id = models.CharField(max_length=100, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-issue_date"]

    def __str__(self):
        return self.name


class EmploymentHistoryRecord(BaseModel):
    class EventType(models.TextChoices):
        HIRED = "HIRED", "Hired"
        PROMOTED = "PROMOTED", "Promoted"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        DEMOTED = "DEMOTED", "Demoted"
        SUSPENDED = "SUSPENDED", "Suspended"
        REINSTATED = "REINSTATED", "Reinstated"
        RESIGNED = "RESIGNED", "Resigned"
        TERMINATED = "TERMINATED", "Terminated"
        RETIRED = "RETIRED", "Retired"

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="employment_history"
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    department = models.ForeignKey(
        "organization.Department", null=True, blank=True, on_delete=models.SET_NULL
    )
    position = models.ForeignKey(
        "organization.Position", null=True, blank=True, on_delete=models.SET_NULL
    )
    branch = models.ForeignKey(
        "organization.Branch", null=True, blank=True, on_delete=models.SET_NULL
    )
    effective_date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-effective_date"]

    def __str__(self):
        return f"{self.employee} - {self.event_type} @ {self.effective_date}"

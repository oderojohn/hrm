from django.db import models

from apps.core.models import BaseModel


class Document(BaseModel):
    """Generic store for employee documents and company-wide documents."""

    class Category(models.TextChoices):
        NATIONAL_ID = "NATIONAL_ID", "National ID"
        PASSPORT = "PASSPORT", "Passport"
        CV = "CV", "CV"
        EMPLOYMENT_CONTRACT = "EMPLOYMENT_CONTRACT", "Employment Contract"
        ACADEMIC_CERTIFICATE = "ACADEMIC_CERTIFICATE", "Academic Certificate"
        PROFESSIONAL_CERTIFICATE = "PROFESSIONAL_CERTIFICATE", "Professional Certificate"
        DRIVING_LICENSE = "DRIVING_LICENSE", "Driving License"
        NDA = "NDA", "NDA"
        KRA_CERTIFICATE = "KRA_CERTIFICATE", "KRA Certificate"
        NSSF_DOCUMENT = "NSSF_DOCUMENT", "NSSF Document"
        SHIF_NHIF_DOCUMENT = "SHIF_NHIF_DOCUMENT", "SHIF/NHIF Document"
        COMPANY_POLICY = "COMPANY_POLICY", "Company Policy"
        OTHER = "OTHER", "Other"

    category = models.CharField(max_length=30, choices=Category.choices)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="documents/%Y/%m/")
    employee = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="Leave blank for a company-wide document.",
    )
    expiry_date = models.DateField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    is_company_document = models.BooleanField(
        default=False,
        help_text="If true, visible to every employee via employee self-service.",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        owner = self.employee.full_name if self.employee else "Company-wide"
        return f"{self.title} ({owner})"

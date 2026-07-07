from django.contrib import admin

from apps.employees.models import (
    Certification,
    Education,
    Employee,
    EmploymentHistoryRecord,
)


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class CertificationInline(admin.TabularInline):
    model = Certification
    extra = 0


class EmploymentHistoryInline(admin.TabularInline):
    model = EmploymentHistoryRecord
    extra = 0


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_number",
        "full_name",
        "department",
        "position",
        "branch",
        "employment_status",
    )
    list_filter = ("department", "branch", "employment_status", "employment_type")
    search_fields = ("employee_number", "first_name", "last_name", "national_id", "email")
    inlines = [EducationInline, CertificationInline, EmploymentHistoryInline]

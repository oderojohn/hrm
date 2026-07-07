from django.contrib import admin

from apps.exit_management.models import ClearanceItem, ExitInterview, ExitProcess


class ClearanceItemInline(admin.TabularInline):
    model = ClearanceItem
    extra = 0
    fields = ["department", "description", "is_cleared", "cleared_by", "cleared_at"]


@admin.register(ExitProcess)
class ExitProcessAdmin(admin.ModelAdmin):
    list_display = [
        "employee",
        "exit_type",
        "resignation_date",
        "last_working_date",
        "status",
    ]
    list_filter = ["status", "exit_type"]
    search_fields = ["employee__first_name", "employee__last_name", "employee__employee_number"]
    inlines = [ClearanceItemInline]


@admin.register(ExitInterview)
class ExitInterviewAdmin(admin.ModelAdmin):
    list_display = [
        "exit_process",
        "conducted_by",
        "interview_date",
        "would_recommend_company",
    ]
    list_filter = ["would_recommend_company"]
    search_fields = [
        "exit_process__employee__first_name",
        "exit_process__employee__last_name",
    ]

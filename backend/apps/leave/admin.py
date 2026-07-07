from django.contrib import admin

from apps.leave.models import (
    LeaveApprovalStep,
    LeaveBalance,
    LeavePolicy,
    LeaveRequest,
    LeaveType,
    WorkflowStep,
    WorkflowTemplate,
)


class LeavePolicyInline(admin.StackedInline):
    model = LeavePolicy
    extra = 0


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_paid", "is_active")
    inlines = [LeavePolicyInline]


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "leave_type", "year", "allocated_days", "used_days")
    list_filter = ("leave_type", "year")
    search_fields = ("employee__first_name", "employee__last_name", "employee__employee_number")


class LeaveApprovalStepInline(admin.TabularInline):
    model = LeaveApprovalStep
    extra = 0


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "leave_type", "start_date", "end_date", "total_days", "status")
    list_filter = ("status", "leave_type")
    search_fields = ("employee__first_name", "employee__last_name")
    inlines = [LeaveApprovalStepInline]


class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 0


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "is_default", "priority")
    list_filter = ("is_active", "is_default")
    search_fields = ("name",)
    filter_horizontal = ("departments", "branches", "leave_types")
    inlines = [WorkflowStepInline]

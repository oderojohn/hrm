from django.contrib import admin

from apps.organization.models import Branch, Department, Position, WorkShift


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "city", "manager", "is_active")
    search_fields = ("name", "code")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "branch", "head", "is_active")
    list_filter = ("branch",)
    search_fields = ("name", "code")


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "department", "is_active")
    search_fields = ("title", "code")


@admin.register(WorkShift)
class WorkShiftAdmin(admin.ModelAdmin):
    list_display = ("name", "start_time", "end_time", "is_active")

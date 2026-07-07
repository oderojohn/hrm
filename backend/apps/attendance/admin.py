from django.contrib import admin

from apps.attendance.models import (
    AttendanceCorrectionRequest,
    AttendanceRecord,
    BreakRecord,
    Device,
    PunchLog,
    QRToken,
)


class BreakRecordInline(admin.TabularInline):
    model = BreakRecord
    extra = 0


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "clock_in", "clock_out", "method", "is_late")
    list_filter = ("method", "is_late", "is_early_departure")
    search_fields = ("employee__first_name", "employee__last_name", "employee__employee_number")
    inlines = [BreakRecordInline]


@admin.register(AttendanceCorrectionRequest)
class AttendanceCorrectionRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "status", "reviewed_by")
    list_filter = ("status",)


@admin.register(QRToken)
class QRTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "branch", "work_shift", "valid_from", "valid_until", "is_active")


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "device_type", "branch", "ip_address", "port", "is_active", "last_synced_at")
    list_filter = ("device_type", "is_active", "branch")


@admin.register(PunchLog)
class PunchLogAdmin(admin.ModelAdmin):
    list_display = ("employee", "device", "timestamp", "event", "method")
    list_filter = ("event", "method", "device")
    search_fields = ("employee__first_name", "employee__last_name", "employee__employee_number")

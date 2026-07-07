from django.contrib import admin

from apps.training.models import TrainingAttendance, TrainingProgram, TrainingSession


class TrainingAttendanceInline(admin.TabularInline):
    model = TrainingAttendance
    extra = 0


@admin.register(TrainingProgram)
class TrainingProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "provider", "duration_hours", "is_active")
    search_fields = ("title", "code", "provider")
    list_filter = ("is_active",)


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ("program", "start_date", "end_date", "location", "trainer", "capacity")
    search_fields = ("program__title", "location", "trainer")
    list_filter = ("program",)
    inlines = [TrainingAttendanceInline]


@admin.register(TrainingAttendance)
class TrainingAttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "session", "status", "completion_date")
    search_fields = ("employee__first_name", "employee__last_name")
    list_filter = ("status", "session__program")

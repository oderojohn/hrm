from django.contrib import admin

from apps.disciplinary.models import DisciplinaryAction, DisciplinaryCase, Hearing


class DisciplinaryActionInline(admin.TabularInline):
    model = DisciplinaryAction
    extra = 0


class HearingInline(admin.TabularInline):
    model = Hearing
    extra = 0


@admin.register(DisciplinaryCase)
class DisciplinaryCaseAdmin(admin.ModelAdmin):
    list_display = ("employee", "case_type", "title", "status", "incident_date")
    list_filter = ("case_type", "status")
    search_fields = ("title", "description", "employee__first_name", "employee__last_name")
    inlines = [DisciplinaryActionInline, HearingInline]

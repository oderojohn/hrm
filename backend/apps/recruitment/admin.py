from django.contrib import admin

from apps.recruitment.models import (
    Application,
    Candidate,
    Interview,
    JobVacancy,
    OfferLetter,
)


class InterviewInline(admin.TabularInline):
    model = Interview
    extra = 0


@admin.register(JobVacancy)
class JobVacancyAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "code",
        "department",
        "branch",
        "employment_type",
        "status",
        "number_of_positions",
        "posted_date",
    )
    list_filter = ("status", "employment_type", "department", "branch")
    search_fields = ("title", "code")


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "source")
    search_fields = ("first_name", "last_name", "email", "phone")
    list_filter = ("source",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("candidate", "vacancy", "status", "applied_at")
    list_filter = ("status", "vacancy")
    search_fields = ("candidate__first_name", "candidate__last_name", "vacancy__title")
    inlines = [InterviewInline]


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ("application", "scheduled_at", "interviewer", "mode", "status", "rating")
    list_filter = ("status", "mode")
    search_fields = ("application__candidate__first_name", "application__candidate__last_name")


@admin.register(OfferLetter)
class OfferLetterAdmin(admin.ModelAdmin):
    list_display = ("application", "position_title", "proposed_start_date", "status", "sent_at")
    list_filter = ("status",)
    search_fields = ("position_title", "application__candidate__first_name")

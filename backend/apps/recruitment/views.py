from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.permissions import IsHRManagerOrAbove
from apps.recruitment.models import (
    Application,
    Candidate,
    Interview,
    JobVacancy,
    OfferLetter,
)
from apps.recruitment.serializers import (
    ApplicationSerializer,
    CandidateSerializer,
    InterviewSerializer,
    JobVacancySerializer,
    OfferLetterSerializer,
)


class WriteRestrictedMixin:
    """Read access for any authenticated user; writes restricted to HR managers and above."""

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsHRManagerOrAbove()]
        return [IsAuthenticated()]


class JobVacancyViewSet(WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = JobVacancy.objects.select_related("department", "branch").all()
    serializer_class = JobVacancySerializer
    filterset_fields = ["department", "branch", "status", "employment_type"]
    search_fields = ["title", "code"]
    ordering_fields = ["posted_date", "closing_date", "title"]
    export_headers = [
        "Title",
        "Code",
        "Department",
        "Branch",
        "Employment Type",
        "Positions",
        "Status",
        "Posted Date",
        "Closing Date",
    ]

    def export_row(self, obj):
        return [
            obj.title,
            obj.code,
            obj.department.name if obj.department else "",
            obj.branch.name if obj.branch else "",
            obj.get_employment_type_display(),
            obj.number_of_positions,
            obj.get_status_display(),
            obj.posted_date,
            obj.closing_date,
        ]


class CandidateViewSet(WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer
    filterset_fields = ["source"]
    search_fields = ["first_name", "last_name", "email", "phone"]
    ordering_fields = ["last_name", "first_name", "created_at"]
    export_headers = ["Full Name", "Email", "Phone", "Source"]

    def export_row(self, obj):
        return [obj.full_name, obj.email, obj.phone, obj.source]


class ApplicationViewSet(WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = Application.objects.select_related("vacancy", "candidate").all()
    serializer_class = ApplicationSerializer
    filterset_fields = ["vacancy", "status"]
    search_fields = ["candidate__first_name", "candidate__last_name", "vacancy__title"]
    ordering_fields = ["applied_at"]
    export_headers = ["Candidate", "Vacancy", "Applied At", "Status"]

    def export_row(self, obj):
        return [obj.candidate.full_name, obj.vacancy.title, obj.applied_at, obj.get_status_display()]


class InterviewViewSet(WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = Interview.objects.select_related("application", "interviewer").all()
    serializer_class = InterviewSerializer
    filterset_fields = ["application", "interviewer", "status", "mode"]
    search_fields = ["location"]
    ordering_fields = ["scheduled_at"]
    export_headers = ["Application", "Scheduled At", "Interviewer", "Mode", "Status", "Rating"]

    def export_row(self, obj):
        return [
            str(obj.application),
            obj.scheduled_at,
            obj.interviewer.full_name if obj.interviewer else "",
            obj.get_mode_display(),
            obj.get_status_display(),
            obj.rating,
        ]


class OfferLetterViewSet(WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = OfferLetter.objects.select_related("application", "application__candidate").all()
    serializer_class = OfferLetterSerializer
    filterset_fields = ["status"]
    search_fields = ["position_title"]
    ordering_fields = ["proposed_start_date", "created_at"]
    export_headers = [
        "Candidate",
        "Position Title",
        "Proposed Start Date",
        "Status",
        "Sent At",
        "Responded At",
    ]

    def export_row(self, obj):
        return [
            obj.application.candidate.full_name,
            obj.position_title,
            obj.proposed_start_date,
            obj.get_status_display(),
            obj.sent_at,
            obj.responded_at,
        ]

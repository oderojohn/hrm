from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.permissions import IsHRManagerOrAbove
from apps.disciplinary.models import DisciplinaryAction, DisciplinaryCase, Hearing
from apps.disciplinary.serializers import (
    DisciplinaryActionSerializer,
    DisciplinaryCaseSerializer,
    HearingSerializer,
)


class WriteRestrictedMixin:
    """Read access for any authenticated user; writes restricted to HR managers and above."""

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsHRManagerOrAbove()]
        return [IsAuthenticated()]


class DisciplinaryCaseViewSet(
    WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet
):
    serializer_class = DisciplinaryCaseSerializer
    filterset_fields = ["employee", "case_type", "status"]
    search_fields = ["title", "description"]
    ordering_fields = ["incident_date", "created_at"]
    export_headers = ["Employee", "Case Type", "Title", "Status", "Incident Date"]

    def get_queryset(self):
        user = self.request.user
        qs = DisciplinaryCase.objects.select_related("employee", "raised_by").prefetch_related(
            "actions", "hearings"
        )
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(employee__department_id=own.department_id)
        return qs.filter(employee=own) if own else qs.none()

    def export_row(self, obj):
        return [
            obj.employee.full_name,
            obj.case_type,
            obj.title,
            obj.status,
            obj.incident_date,
        ]


class DisciplinaryActionViewSet(
    WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet
):
    serializer_class = DisciplinaryActionSerializer
    filterset_fields = ["case"]
    export_headers = ["Case", "Action Type", "Issued Date", "Issued By"]

    def get_queryset(self):
        user = self.request.user
        qs = DisciplinaryAction.objects.select_related("case", "case__employee", "issued_by")
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(case__employee__department_id=own.department_id)
        return qs.filter(case__employee=own) if own else qs.none()

    def export_row(self, obj):
        issued_by = obj.issued_by.full_name if obj.issued_by else ""
        return [str(obj.case), obj.action_type, obj.issued_date, issued_by]


class HearingViewSet(WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    serializer_class = HearingSerializer
    filterset_fields = ["case"]
    export_headers = ["Case", "Scheduled Date", "Status", "Outcome"]

    def get_queryset(self):
        user = self.request.user
        qs = Hearing.objects.select_related("case", "case__employee").prefetch_related(
            "panel_members"
        )
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(case__employee__department_id=own.department_id)
        return qs.filter(case__employee=own) if own else qs.none()

    def export_row(self, obj):
        return [str(obj.case), obj.scheduled_date, obj.status, obj.outcome]

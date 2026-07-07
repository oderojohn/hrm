from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.permissions import IsHRManagerOrAbove
from apps.training.models import TrainingAttendance, TrainingProgram, TrainingSession
from apps.training.serializers import (
    TrainingAttendanceSerializer,
    TrainingProgramSerializer,
    TrainingSessionSerializer,
)


class WriteRestrictedMixin:
    """Read access for any authenticated user; writes restricted to HR managers and above."""

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsHRManagerOrAbove()]
        return [IsAuthenticated()]


class TrainingProgramViewSet(
    WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet
):
    queryset = TrainingProgram.objects.all()
    serializer_class = TrainingProgramSerializer
    filterset_fields = ["is_active"]
    search_fields = ["title", "code"]
    ordering_fields = ["title"]
    export_headers = ["Title", "Code", "Provider", "Duration (Hours)", "Active"]

    def export_row(self, obj):
        return [obj.title, obj.code, obj.provider, obj.duration_hours, obj.is_active]


class TrainingSessionViewSet(
    WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet
):
    queryset = TrainingSession.objects.select_related("program").all()
    serializer_class = TrainingSessionSerializer
    filterset_fields = ["program"]
    search_fields = ["location", "trainer"]
    ordering_fields = ["start_date"]
    export_headers = ["Program", "Start Date", "End Date", "Location", "Trainer"]

    def export_row(self, obj):
        return [
            obj.program.title,
            obj.start_date,
            obj.end_date,
            obj.location,
            obj.trainer,
        ]


class TrainingAttendanceViewSet(AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    serializer_class = TrainingAttendanceSerializer
    filterset_fields = ["session", "employee", "status"]
    export_headers = ["Employee", "Session", "Status", "Completion Date"]

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsHRManagerOrAbove()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = TrainingAttendance.objects.select_related(
            "session", "session__program", "employee"
        ).all()
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(employee__department_id=own.department_id)
        return qs.filter(employee=own) if own else qs.none()

    def export_row(self, obj):
        return [
            obj.employee.full_name,
            str(obj.session),
            obj.status,
            obj.completion_date,
        ]

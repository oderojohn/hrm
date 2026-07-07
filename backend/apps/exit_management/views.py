from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.permissions import IsHRManagerOrAbove
from apps.exit_management.models import ClearanceItem, ExitInterview, ExitProcess
from apps.exit_management.serializers import (
    ClearanceItemSerializer,
    ExitInterviewSerializer,
    ExitProcessSerializer,
)


class ExitProcessViewSet(AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = ExitProcess.objects.select_related("employee").prefetch_related(
        "clearance_items"
    )
    serializer_class = ExitProcessSerializer
    permission_classes = [IsHRManagerOrAbove]
    filterset_fields = ["status", "exit_type", "employee"]
    search_fields = ["employee__first_name", "employee__last_name"]
    ordering_fields = ["last_working_date", "created_at"]
    export_headers = ["Employee", "Exit Type", "Last Working Date", "Status"]

    def export_row(self, obj):
        return [
            obj.employee.full_name,
            obj.get_exit_type_display(),
            obj.last_working_date,
            obj.get_status_display(),
        ]

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        exit_process = self.get_object()
        if exit_process.clearance_items.filter(is_cleared=False).exists():
            return Response(
                {"detail": "All clearance items must be cleared first."}, status=400
            )
        exit_process.status = ExitProcess.Status.COMPLETED
        exit_process.save()
        employee = exit_process.employee
        if employee.user_id:
            employee.user.is_active = False
            employee.user.save(update_fields=["is_active"])
        return Response(ExitProcessSerializer(exit_process).data)


class ClearanceItemViewSet(AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = ClearanceItem.objects.select_related("exit_process", "cleared_by")
    serializer_class = ClearanceItemSerializer
    permission_classes = [IsHRManagerOrAbove]
    filterset_fields = ["exit_process", "is_cleared"]
    search_fields = ["department", "description"]
    export_headers = ["Exit Process", "Department", "Description", "Cleared"]

    def export_row(self, obj):
        return [
            str(obj.exit_process),
            obj.department,
            obj.description,
            obj.is_cleared,
        ]

    @action(detail=True, methods=["post"])
    def clear(self, request, pk=None):
        item = self.get_object()
        item.is_cleared = True
        item.cleared_by = getattr(request.user, "employee", None)
        item.cleared_at = timezone.now()
        item.save()
        return Response(ClearanceItemSerializer(item).data)


class ExitInterviewViewSet(AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = ExitInterview.objects.select_related("exit_process", "conducted_by")
    serializer_class = ExitInterviewSerializer
    permission_classes = [IsHRManagerOrAbove]
    filterset_fields = ["exit_process"]
    export_headers = ["Exit Process", "Conducted By", "Interview Date", "Recommend"]

    def export_row(self, obj):
        return [
            str(obj.exit_process),
            obj.conducted_by.full_name if obj.conducted_by else "",
            obj.interview_date,
            obj.would_recommend_company,
        ]

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.assets.models import (
    Asset,
    AssetAssignment,
    AssetMaintenanceRecord,
    LostAssetReport,
)
from apps.assets.serializers import (
    AssetAssignmentSerializer,
    AssetMaintenanceRecordSerializer,
    AssetSerializer,
    LostAssetReportSerializer,
)
from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.models import AuditLog
from apps.core.permissions import IsHRManagerOrAbove


class WriteRestrictedMixin:
    """Read access for any authenticated user; writes restricted to HR managers and above."""

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsHRManagerOrAbove()]
        return [IsAuthenticated()]


class AssetViewSet(WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = Asset.objects.select_related("branch").all()
    serializer_class = AssetSerializer
    filterset_fields = ["category", "status", "branch", "condition"]
    search_fields = ["asset_tag", "name", "serial_number"]
    ordering_fields = ["asset_tag", "name"]
    export_headers = ["Asset Tag", "Name", "Category", "Condition", "Status", "Branch"]

    def export_row(self, obj):
        return [
            obj.asset_tag,
            obj.name,
            obj.category,
            obj.condition,
            obj.status,
            obj.branch.name if obj.branch else "",
        ]


class AssetAssignmentViewSet(
    WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet
):
    serializer_class = AssetAssignmentSerializer
    filterset_fields = ["asset", "employee"]
    search_fields = ["notes"]
    ordering_fields = ["assigned_date"]
    export_headers = ["Asset", "Employee", "Assigned Date", "Returned At"]

    def get_queryset(self):
        user = self.request.user
        qs = AssetAssignment.objects.select_related("asset", "employee")
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(employee__department_id=own.department_id)
        return qs.filter(employee=own) if own else qs.none()

    def export_row(self, obj):
        return [
            obj.asset.asset_tag,
            obj.employee.full_name,
            obj.assigned_date,
            obj.returned_at,
        ]

    def perform_create(self, serializer):
        instance = serializer.save()
        asset = instance.asset
        asset.status = Asset.Status.ASSIGNED
        asset.save(update_fields=["status"])
        self._log(AuditLog.Action.CREATE, instance)

    def perform_update(self, serializer):
        previous_returned_at = serializer.instance.returned_at
        instance = serializer.save()
        if previous_returned_at is None and instance.returned_at is not None:
            asset = instance.asset
            asset.status = Asset.Status.AVAILABLE
            asset.save(update_fields=["status"])
        self._log(AuditLog.Action.UPDATE, instance)


class AssetMaintenanceRecordViewSet(
    WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet
):
    queryset = AssetMaintenanceRecord.objects.select_related("asset").all()
    serializer_class = AssetMaintenanceRecordSerializer
    filterset_fields = ["asset", "status"]
    search_fields = ["description"]
    ordering_fields = ["reported_date"]
    export_headers = ["Asset", "Reported Date", "Status", "Resolved Date"]

    def export_row(self, obj):
        return [obj.asset.asset_tag, obj.reported_date, obj.status, obj.resolved_date]


class LostAssetReportViewSet(
    WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet
):
    queryset = LostAssetReport.objects.select_related("asset", "employee").all()
    serializer_class = LostAssetReportSerializer
    filterset_fields = ["asset", "employee", "status"]
    search_fields = ["circumstances"]
    ordering_fields = ["reported_date"]
    export_headers = ["Asset", "Employee", "Reported Date", "Status"]

    def export_row(self, obj):
        return [
            obj.asset.asset_tag,
            obj.employee.full_name if obj.employee else "",
            obj.reported_date,
            obj.status,
        ]

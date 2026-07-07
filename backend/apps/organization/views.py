from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.models import AuditLog
from apps.core.permissions import IsHRManagerOrAbove, IsSuperAdmin
from apps.employees.models import Employee
from apps.organization.models import Branch, Department, Position, WorkShift
from apps.organization.serializers import (
    BranchSerializer,
    DepartmentSerializer,
    PositionSerializer,
    WorkShiftSerializer,
)


class WriteRestrictedMixin:
    """Read access for any authenticated user; writes restricted to super admins."""

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsSuperAdmin()]
        return [IsAuthenticated()]


class BranchViewSet(WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = Branch.objects.select_related("manager").all()
    serializer_class = BranchSerializer
    filterset_fields = ["is_active"]
    search_fields = ["name", "code", "city"]
    ordering_fields = ["name"]
    export_headers = ["Name", "Code", "City", "Phone", "Active"]

    def export_row(self, obj):
        return [obj.name, obj.code, obj.city, obj.phone, obj.is_active]


class DepartmentViewSet(WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = Department.objects.select_related("branch", "head").all()
    serializer_class = DepartmentSerializer
    filterset_fields = ["branch", "is_active", "parent_department"]
    search_fields = ["name", "code"]
    ordering_fields = ["name"]
    export_headers = ["Name", "Code", "Branch", "Active"]

    def export_row(self, obj):
        return [obj.name, obj.code, obj.branch.name, obj.is_active]


class PositionViewSet(WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = Position.objects.select_related("department").all()
    serializer_class = PositionSerializer
    filterset_fields = ["department", "is_active"]
    search_fields = ["title", "code"]
    ordering_fields = ["title"]
    export_headers = ["Title", "Code", "Department", "Active"]

    def export_row(self, obj):
        department_name = obj.department.name if obj.department else ""
        return [obj.title, obj.code, department_name, obj.is_active]


class WorkShiftViewSet(WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = WorkShift.objects.all()
    serializer_class = WorkShiftSerializer
    filterset_fields = ["is_active"]
    search_fields = ["name"]
    ordering_fields = ["name"]
    export_headers = ["Name", "Start", "End", "Active"]

    def export_row(self, obj):
        return [obj.name, obj.start_time, obj.end_time, obj.is_active]

    def get_permissions(self):
        if self.action == "assign_employees":
            return [IsHRManagerOrAbove()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], url_path="assign-employees")
    def assign_employees(self, request, pk=None):
        shift = self.get_object()
        employee_ids = request.data.get("employee_ids", [])
        if not isinstance(employee_ids, list) or not employee_ids:
            return Response({"detail": "employee_ids must be a non-empty list."}, status=400)

        updated = Employee.objects.filter(id__in=employee_ids).update(work_shift=shift)
        self._log(
            AuditLog.Action.UPDATE,
            shift,
            {"event": "bulk_shift_assign", "employee_ids": employee_ids, "count": updated},
        )
        return Response({"detail": f"Assigned {updated} employee(s) to {shift.name}.", "updated_count": updated})

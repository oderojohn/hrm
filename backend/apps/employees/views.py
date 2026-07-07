from django.utils.crypto import get_random_string
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.models import AuditLog
from apps.core.permissions import IsHRManagerOrAbove, IsSelfOrManager
from apps.employees.models import (
    Certification,
    Education,
    Employee,
    EmploymentHistoryRecord,
)
from apps.employees.serializers import (
    CertificationSerializer,
    EducationSerializer,
    EmployeeDetailSerializer,
    EmployeeListSerializer,
    EmployeeSelfServiceSerializer,
    EmploymentHistoryRecordSerializer,
)


class EmployeeViewSet(AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    filterset_fields = ["department", "branch", "position", "employment_status", "employment_type"]
    search_fields = ["first_name", "last_name", "employee_number", "email", "national_id"]
    ordering_fields = ["employee_number", "employment_date", "last_name"]
    export_headers = ["Employee No.", "Full Name", "Department", "Position", "Status"]

    def get_queryset(self):
        user = self.request.user
        qs = Employee.objects.select_related(
            "department", "position", "branch", "reporting_manager"
        ).prefetch_related("education", "certifications", "employment_history")

        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs

        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER:
            if own and own.department_id:
                return qs.filter(department_id=own.department_id)
            return qs.none()

        return qs.filter(pk=own.pk) if own else qs.none()

    def get_serializer_class(self):
        if self.action == "list":
            return EmployeeListSerializer
        return EmployeeDetailSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsHRManagerOrAbove()]
        if self.action in ("retrieve", "profile"):
            return [IsAuthenticated(), IsSelfOrManager()]
        return [IsAuthenticated()]

    def export_row(self, obj):
        department_name = obj.department.name if obj.department else ""
        position_title = obj.position.title if obj.position else ""
        return [obj.employee_number, obj.full_name, department_name, position_title, obj.employment_status]

    def _push_to_device_best_effort(self, employee):
        """Provisioning a live biometric device is best-effort — a device outage
        must never block saving an employee record in the database."""
        try:
            from apps.attendance.services import push_employee_to_device

            push_employee_to_device(employee)
        except Exception:
            pass

    def perform_create(self, serializer):
        instance = serializer.save()
        self._log(AuditLog.Action.CREATE, instance)
        self._push_to_device_best_effort(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._log(AuditLog.Action.UPDATE, instance)
        self._push_to_device_best_effort(instance)

    @action(detail=True, methods=["post"], permission_classes=[IsHRManagerOrAbove], url_path="push-to-device")
    def push_to_device(self, request, pk=None):
        employee = self.get_object()
        from apps.attendance.services import push_employee_to_device

        try:
            device_user_id = push_employee_to_device(employee)
        except Exception as exc:
            return Response({"detail": f"Could not push to device: {exc}"}, status=502)
        return Response({"detail": "Pushed to device.", "device_user_id": device_user_id})

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        """Self-service view/edit of the current user's own employee record —
        a deliberately narrow field set (see EmployeeSelfServiceSerializer),
        independent of the HR-only create/update/destroy permissions above."""
        employee = getattr(request.user, "employee", None)
        if not employee:
            return Response({"detail": "No employee profile linked to this account."}, status=404)

        if request.method == "GET":
            return Response(EmployeeSelfServiceSerializer(employee).data)

        serializer = EmployeeSelfServiceSerializer(employee, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self._log(AuditLog.Action.UPDATE, employee, {"event": "self_service_update"})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsHRManagerOrAbove], url_path="create-account")
    def create_account(self, request, pk=None):
        employee = self.get_object()
        if employee.user_id:
            return Response({"detail": "This employee already has a linked account."}, status=400)

        email = (request.data.get("email") or employee.email or "").strip().lower()
        if not email:
            return Response({"detail": "An email address is required to create a login account."}, status=400)
        if User.objects.filter(email=email).exists():
            return Response({"detail": "A user with this email already exists."}, status=400)

        role = request.data.get("role", User.Role.EMPLOYEE)
        if role not in dict(User.Role.choices):
            return Response({"detail": "Invalid role."}, status=400)
        if role == User.Role.SUPER_ADMIN and request.user.role != User.Role.SUPER_ADMIN:
            return Response({"detail": "Only a Super Administrator can assign that role."}, status=403)

        password = request.data.get("password") or get_random_string(10)

        user = User.objects.create_user(
            email=email,
            password=password,
            role=role,
            first_name=employee.first_name,
            last_name=employee.last_name,
        )
        employee.user = user
        employee.email = employee.email or email
        employee.save(update_fields=["user", "email"])
        self._log(AuditLog.Action.OTHER, employee, {"event": "account_created", "email": email, "role": role})

        return Response(
            {"detail": "Account created.", "email": email, "password": password, "user_id": user.id}, status=201
        )

    @action(detail=True, methods=["post"], permission_classes=[IsHRManagerOrAbove], url_path="reset-password")
    def reset_password(self, request, pk=None):
        employee = self.get_object()
        if not employee.user_id:
            return Response({"detail": "This employee has no linked account."}, status=400)

        password = request.data.get("password") or get_random_string(10)
        employee.user.set_password(password)
        employee.user.save(update_fields=["password"])
        self._log(AuditLog.Action.OTHER, employee, {"event": "password_reset"})

        return Response({"detail": "Password reset.", "email": employee.user.email, "password": password})

    @action(detail=True, methods=["get"])
    def profile(self, request, pk=None):
        employee = self.get_object()

        from apps.assets.serializers import AssetAssignmentSerializer
        from apps.attendance.serializers import AttendanceRecordSerializer
        from apps.disciplinary.serializers import DisciplinaryCaseSerializer
        from apps.leave.serializers import LeaveRequestSerializer
        from apps.performance.serializers import PerformanceReviewSerializer
        from apps.training.serializers import TrainingAttendanceSerializer

        data = EmployeeDetailSerializer(employee).data
        data["leave_history"] = LeaveRequestSerializer(
            employee.leave_requests.all()[:20], many=True
        ).data
        data["attendance_history"] = AttendanceRecordSerializer(
            employee.attendance_records.all()[:30], many=True
        ).data
        data["performance_reviews"] = PerformanceReviewSerializer(
            employee.performance_reviews.all()[:10], many=True
        ).data
        data["disciplinary_records"] = DisciplinaryCaseSerializer(
            employee.disciplinary_cases.all()[:10], many=True
        ).data
        data["training_records"] = TrainingAttendanceSerializer(
            employee.training_records.all()[:10], many=True
        ).data
        data["assigned_assets"] = AssetAssignmentSerializer(
            employee.asset_assignments.filter(returned_at__isnull=True), many=True
        ).data
        return Response(data)


class EducationViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = Education.objects.select_related("employee").all()
    serializer_class = EducationSerializer
    filterset_fields = ["employee"]
    permission_classes = [IsHRManagerOrAbove]


class CertificationViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = Certification.objects.select_related("employee").all()
    serializer_class = CertificationSerializer
    filterset_fields = ["employee"]
    permission_classes = [IsHRManagerOrAbove]


class EmploymentHistoryViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = EmploymentHistoryRecord.objects.select_related("employee").all()
    serializer_class = EmploymentHistoryRecordSerializer
    filterset_fields = ["employee", "event_type"]
    permission_classes = [IsHRManagerOrAbove]

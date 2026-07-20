import secrets
from datetime import date
from types import SimpleNamespace

import django_filters
from django.conf import settings
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attendance import notifications
from apps.attendance.authentication import SyncAgentAuthentication
from apps.attendance.models import (
    AttendanceCorrectionRequest,
    AttendanceRecord,
    AttendanceSettings,
    Device,
    PunchLog,
    QRToken,
    SyncAgent,
    SyncEvent,
)
from apps.attendance.permissions import IsSyncAgent
from apps.attendance.serializers import (
    AttendanceCorrectionRequestSerializer,
    AttendanceRecordSerializer,
    AttendanceSettingsSerializer,
    DeviceSerializer,
    PunchLogSerializer,
    QRTokenSerializer,
    SyncAgentSerializer,
    SyncEventSerializer,
)
from apps.attendance.utils import evaluate_clock_in as _evaluate_clock_in
from apps.attendance.utils import evaluate_clock_out as _evaluate_clock_out
from apps.attendance.utils import is_expected_working_day
from apps.core.exports import export_queryset
from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.models import AuditLog, PublicHoliday
from apps.core.permissions import IsHRManagerOrAbove, IsSuperAdmin
from apps.employees.models import Employee


def _generate_agent_key():
    """Returns (raw_key, key_prefix, key_hash) for a new/rotated SyncAgent key."""
    import hashlib

    raw_key = f"eak_{secrets.token_urlsafe(32)}"
    return raw_key, raw_key[:12], hashlib.sha256(raw_key.encode()).hexdigest()


class AttendanceRecordFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    branch = django_filters.NumberFilter(field_name="employee__branch_id")
    department = django_filters.NumberFilter(field_name="employee__department_id")

    class Meta:
        model = AttendanceRecord
        fields = ["employee", "date", "method", "is_late", "date_from", "date_to", "branch", "department"]


class AttendanceRecordViewSet(AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    serializer_class = AttendanceRecordSerializer
    filterset_class = AttendanceRecordFilter
    ordering_fields = ["date"]
    export_headers = ["Employee", "Date", "Clock In", "Clock Out", "Device", "Late", "Overtime (min)"]

    def get_queryset(self):
        user = self.request.user
        qs = AttendanceRecord.objects.select_related("employee", "device").prefetch_related("breaks")
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(employee__department_id=own.department_id)
        return qs.filter(employee=own) if own else qs.none()

    def export_row(self, obj):
        return [
            obj.employee.full_name,
            obj.date,
            obj.clock_in,
            obj.clock_out,
            obj.device.name if obj.device else "",
            obj.is_late,
            obj.overtime_minutes,
        ]


class AttendanceDashboardView(APIView):
    """Attendance-specific dashboard counts + a recent-activity feed — kept
    separate from apps.reports.views.DashboardView (the company-wide one)
    since this module wants late-arrivals/early-departures tiles and a
    punch-level activity feed that the general dashboard has no room for.
    """

    permission_classes = [IsHRManagerOrAbove]

    def get(self, request):
        from apps.leave.models import LeaveRequest

        today = timezone.now().date()
        employees = Employee.objects.filter(employment_status=Employee.EmploymentStatus.ACTIVE)
        active_ids = employees.values_list("id", flat=True)

        present_today = AttendanceRecord.objects.filter(
            employee_id__in=active_ids, date=today, clock_in__isnull=False
        ).count()
        on_leave_today = LeaveRequest.objects.filter(
            employee_id__in=active_ids,
            status=LeaveRequest.Status.APPROVED,
            start_date__lte=today,
            end_date__gte=today,
        ).count()
        absent_today = max(employees.count() - present_today - on_leave_today, 0)
        late_today = AttendanceRecord.objects.filter(
            employee_id__in=active_ids, date=today, is_late=True
        ).count()
        early_departures_today = AttendanceRecord.objects.filter(
            employee_id__in=active_ids, date=today, is_early_departure=True
        ).count()

        recent_activity = [
            {
                "employee_name": p.employee.full_name,
                "event": p.event,
                "timestamp": p.timestamp,
                "device_name": p.device.name if p.device else None,
            }
            for p in PunchLog.objects.select_related("employee", "device").order_by("-timestamp")[:15]
        ]

        return Response(
            {
                "total_employees": employees.count(),
                "present_today": present_today,
                "absent_today": absent_today,
                "on_leave_today": on_leave_today,
                "late_arrivals_today": late_today,
                "early_departures_today": early_departures_today,
                "recent_activity": recent_activity,
            }
        )


class DailyAttendanceView(APIView):
    """Roster-based daily attendance: one row per active employee for a given
    date (default today), including employees who are Absent or On Leave —
    unlike AttendanceRecordViewSet, which only returns rows that already
    exist for employees who actually punched that day.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.leave.models import LeaveRequest
        from apps.reports.views import _scoped_employees

        raw_date = request.query_params.get("date")
        day = date.fromisoformat(raw_date) if raw_date else timezone.now().date()

        employees = _scoped_employees(request.user).filter(
            employment_status=Employee.EmploymentStatus.ACTIVE
        )
        department_param = request.query_params.get("department")
        branch_param = request.query_params.get("branch")
        employee_param = request.query_params.get("employee")
        if department_param:
            employees = employees.filter(department_id=department_param)
        if branch_param:
            employees = employees.filter(branch_id=branch_param)
        if employee_param:
            employees = employees.filter(id=employee_param)
        employees = employees.select_related("department", "work_shift")

        records = {
            r.employee_id: r for r in AttendanceRecord.objects.filter(employee__in=employees, date=day)
        }
        on_leave_ids = set(
            LeaveRequest.objects.filter(
                employee__in=employees,
                status=LeaveRequest.Status.APPROVED,
                start_date__lte=day,
                end_date__gte=day,
            ).values_list("employee_id", flat=True)
        )
        holiday_dates = {day} if PublicHoliday.objects.filter(date=day).exists() else set()

        rows = []
        for employee in employees:
            record = records.get(employee.id)
            if employee.id in on_leave_ids:
                status_label = "ON_LEAVE"
            elif record and record.clock_in:
                status_label = "LATE" if record.is_late else "PRESENT"
            elif is_expected_working_day(employee, day, holiday_dates):
                status_label = "ABSENT"
            else:
                status_label = "OFF"

            working_hours = None
            if record and record.clock_in and record.clock_out:
                working_hours = round((record.clock_out - record.clock_in).total_seconds() / 3600, 2)

            rows.append(
                {
                    "employee_id": employee.id,
                    "employee_number": employee.employee_number,
                    "employee_name": employee.full_name,
                    "department_name": employee.department.name if employee.department else None,
                    "shift_name": employee.work_shift.name if employee.work_shift else None,
                    "clock_in": record.clock_in if record else None,
                    "clock_out": record.clock_out if record else None,
                    "working_hours": working_hours,
                    "status": status_label,
                }
            )

        export_headers = [
            "Employee No.",
            "Employee",
            "Department",
            "Shift",
            "Clock In",
            "Clock Out",
            "Working Hours",
            "Status",
        ]

        def export_row(r):
            return [
                r["employee_number"],
                r["employee_name"],
                r["department_name"] or "",
                r["shift_name"] or "",
                r["clock_in"],
                r["clock_out"],
                r["working_hours"],
                r["status"],
            ]

        export_response = export_queryset(request, rows, export_headers, export_row, "daily_attendance")
        if export_response is not None:
            return export_response

        return Response({"date": day.isoformat(), "count": len(rows), "results": rows})


class AttendanceSettingsView(APIView):
    """Singleton company-wide attendance settings — see AttendanceSettings."""

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT"):
            return [IsHRManagerOrAbove()]
        return [IsAuthenticated()]

    def get(self, request):
        return Response(AttendanceSettingsSerializer(AttendanceSettings.get_solo()).data)

    def patch(self, request):
        instance = AttendanceSettings.get_solo()
        serializer = AttendanceSettingsSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DeviceViewSet(AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = Device.objects.select_related("branch").all()
    serializer_class = DeviceSerializer
    filterset_fields = ["is_active", "branch"]
    search_fields = ["name"]
    ordering_fields = ["name"]
    export_headers = ["Name", "Branch", "IP Address", "Port", "Active", "Last Synced"]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [IsHRManagerOrAbove()]

    def export_row(self, obj):
        return [
            obj.name,
            obj.branch.name if obj.branch else "",
            obj.ip_address,
            obj.port,
            obj.is_active,
            obj.last_synced_at,
        ]


class SyncAgentViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """Cloud-side management of local sync agent installations — this is
    where a Super Admin generates/revokes the API keys the Tkinter desktop
    agent authenticates with (see apps.attendance.authentication).
    """

    queryset = SyncAgent.objects.select_related("branch").all()
    serializer_class = SyncAgentSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ["is_active", "branch"]
    search_fields = ["name"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw_key, key_prefix, key_hash = _generate_agent_key()
        agent = serializer.save(key_prefix=key_prefix, key_hash=key_hash)
        self._log(AuditLog.Action.CREATE, agent)
        return Response(
            {"detail": "Agent created.", "api_key": raw_key, **self.get_serializer(agent).data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="regenerate-key")
    def regenerate_key(self, request, pk=None):
        agent = self.get_object()
        raw_key, key_prefix, key_hash = _generate_agent_key()
        agent.key_prefix = key_prefix
        agent.key_hash = key_hash
        agent.save(update_fields=["key_prefix", "key_hash"])
        self._log(AuditLog.Action.OTHER, agent, {"event": "key_regenerated"})
        return Response({"detail": "Key regenerated.", "api_key": raw_key})


class SyncEventViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only log of every communication from every sync agent — auth
    failures, pushes, and errors — for the "admin can see everything" view.
    """

    queryset = SyncEvent.objects.select_related("agent").all()
    serializer_class = SyncEventSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ["agent", "event_type", "status"]
    ordering_fields = ["created_at"]


class SyncPushView(APIView):
    """Receives a batch of newly-seen device users/punches from a local sync
    agent and ingests them via the same sync_employees_from_list/ingest_punches
    helpers the ZK-device pull path uses, so "cloud pulls from device" and
    "agent pushes to cloud" share one ingestion pipeline, not two.
    """

    authentication_classes = [SyncAgentAuthentication]
    permission_classes = [IsSyncAgent]

    def post(self, request):
        from apps.attendance.services import ingest_punches, sync_employees_from_list

        agent = request.auth
        device_name = request.data.get("device_name") or "Unnamed Device"
        device_ip = request.data.get("device_ip")
        device_type = (
            Device.DeviceType.HIKVISION
            if request.data.get("device_type") == "hikvision"
            else Device.DeviceType.ZKTECO
        )
        users_payload = request.data.get("users", [])
        punches_payload = request.data.get("punches", [])

        try:
            device, _ = Device.objects.get_or_create(
                name=device_name,
                defaults={
                    "ip_address": device_ip,
                    "branch": agent.branch,
                    "device_type": device_type,
                },
            )
            device.ip_address = device_ip or device.ip_address
            device.device_type = device_type
            device.last_synced_at = timezone.now()
            device.save(update_fields=["ip_address", "device_type", "last_synced_at"])

            employee_summary = sync_employees_from_list(
                (SimpleNamespace(user_id=u.get("user_id"), name=u.get("name", "")) for u in users_payload),
                branch=agent.branch,
            )

            device_id_to_employee = {
                e.device_user_id: e
                for e in Employee.objects.exclude(device_user_id__isnull=True).exclude(device_user_id="")
            }
            punches = []
            unmatched = set()
            for p in punches_payload:
                device_user_id = str(p.get("user_id", "")).strip()
                employee = device_id_to_employee.get(device_user_id)
                if not employee:
                    unmatched.add(device_user_id)
                    continue
                when = timezone.datetime.fromisoformat(p["timestamp"])
                punches.append((employee, when, p.get("raw_status")))

            attendance_summary = ingest_punches(punches, device=device)
            attendance_summary["unmatched_device_user_ids"] = sorted(unmatched)
        except Exception as exc:
            SyncEvent.objects.create(
                agent=agent,
                event_type=SyncEvent.EventType.ERROR,
                status=SyncEvent.Status.FAILED,
                summary=f"Push from {device_name} failed: {exc}",
                payload={"error": str(exc)},
                ip_address=request.META.get("REMOTE_ADDR"),
            )
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        summary = f"{attendance_summary['punches_created']} new punch(es) from {device_name}"
        SyncEvent.objects.create(
            agent=agent,
            event_type=SyncEvent.EventType.PUSH,
            status=SyncEvent.Status.SUCCESS,
            summary=summary,
            payload={"employees": employee_summary, "attendance": attendance_summary},
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response({"detail": summary, "employees": employee_summary, "attendance": attendance_summary})


class PunchLogFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name="timestamp", lookup_expr="date__gte")
    date_to = django_filters.DateFilter(field_name="timestamp", lookup_expr="date__lte")

    class Meta:
        model = PunchLog
        fields = ["employee", "device", "date_from", "date_to"]


class PunchLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PunchLogSerializer
    filterset_class = PunchLogFilter
    ordering_fields = ["timestamp"]

    def get_queryset(self):
        user = self.request.user
        qs = PunchLog.objects.select_related("employee", "device")
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(employee__department_id=own.department_id)
        return qs.filter(employee=own) if own else qs.none()


class AttendanceDeviceWebhookView(APIView):
    """Ingest punches from external biometric/face-recognition devices.

    Authenticated with a shared secret header rather than a user session,
    since the caller is a device/integration, not a logged-in person.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        secret = request.headers.get("X-Device-Secret")
        if not settings.DEVICE_WEBHOOK_SECRET or secret != settings.DEVICE_WEBHOOK_SECRET:
            return Response({"detail": "Invalid device credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        employee_number = request.data.get("employee_number")
        event = request.data.get("event", "IN").upper()
        method = request.data.get("method", AttendanceRecord.Method.BIOMETRIC)
        raw_timestamp = request.data.get("timestamp")
        when = timezone.datetime.fromisoformat(raw_timestamp) if raw_timestamp else timezone.now()
        if timezone.is_naive(when):
            when = timezone.make_aware(when)

        try:
            employee = Employee.objects.get(employee_number=employee_number)
        except Employee.DoesNotExist:
            return Response({"detail": "Unknown employee number."}, status=404)

        device_id = request.data.get("device_id")
        device = Device.objects.filter(pk=device_id, is_active=True).first() if device_id else None

        record, _ = AttendanceRecord.objects.get_or_create(
            employee=employee, date=when.date(), defaults={"method": method}
        )
        if device:
            record.device = device

        # Every individual punch is kept, even ones that don't move clock_in/out
        # (e.g. a 3rd or 4th punch in a day) — see PunchLog.
        PunchLog.objects.get_or_create(
            employee=employee,
            device=device,
            timestamp=when,
            defaults={
                "event": PunchLog.Event.IN if event == "IN" else (PunchLog.Event.OUT if event == "OUT" else PunchLog.Event.UNKNOWN),
                "method": method,
            },
        )

        # First clock-in / last clock-out rule, consistent with the ZKTeco batch
        # sync (apps.attendance.services.sync_attendance_from_device): the
        # earliest IN of the day wins, the latest OUT of the day wins.
        if event == "OUT":
            if not record.clock_out or when > record.clock_out:
                record.clock_out = when
                _evaluate_clock_out(record, employee, when)
        else:
            if not record.clock_in or when < record.clock_in:
                record.clock_in = when
                record.method = method
                _evaluate_clock_in(record, employee, when)
        record.save()
        return Response(AttendanceRecordSerializer(record).data, status=201)


class ZKTecoSyncView(APIView):
    """Pulls enrolled users and attendance logs from the ZKTeco device on demand.

    The same sync logic also runs on a schedule via the `sync_zkteco` management
    command (see apps/attendance/management/commands/sync_zkteco.py).
    """

    permission_classes = [IsHRManagerOrAbove]

    def post(self, request):
        from apps.attendance.services import sync_all_devices

        if not Device.objects.filter(is_active=True).exists():
            return Response(
                {"detail": "No active devices configured."}, status=status.HTTP_400_BAD_REQUEST
            )

        results = sync_all_devices()
        return Response({"devices_synced": len(results), "results": results})


class AttendanceCorrectionRequestViewSet(AuditLogMixin, viewsets.ModelViewSet):
    serializer_class = AttendanceCorrectionRequestSerializer
    filterset_fields = ["employee", "status"]

    def get_queryset(self):
        user = self.request.user
        qs = AttendanceCorrectionRequest.objects.select_related("employee", "reviewed_by", "supervisor")

        # Any employee who is someone's reporting_manager gets an approval
        # inbox here, regardless of role — "Supervisor" isn't a role, it's
        # whoever a correction's employee reports to.
        if self.request.query_params.get("pending_supervisor_approval") == "true":
            own = getattr(user, "employee", None)
            return (
                qs.filter(supervisor=own, supervisor_status=AttendanceCorrectionRequest.SupervisorStatus.PENDING)
                if own
                else qs.none()
            )

        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(employee__department_id=own.department_id)
        return qs.filter(employee=own) if own else qs.none()

    def perform_create(self, serializer):
        employee = getattr(self.request.user, "employee", None)
        supervisor = employee.reporting_manager if employee else None
        correction = serializer.save(
            employee=employee,
            supervisor=supervisor,
            supervisor_status=(
                AttendanceCorrectionRequest.SupervisorStatus.PENDING
                if supervisor
                else AttendanceCorrectionRequest.SupervisorStatus.SKIPPED
            ),
        )
        notifications.notify_submitted(correction)

    def _can_act_as_supervisor(self, request, correction):
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        actor = getattr(request.user, "employee", None)
        return bool(actor and correction.supervisor_id == actor.id)

    @action(detail=True, methods=["post"], url_path="supervisor-approve")
    def supervisor_approve(self, request, pk=None):
        correction = self.get_object()
        if not self._can_act_as_supervisor(request, correction):
            return Response({"detail": "Not authorized to act on this correction."}, status=403)
        if correction.supervisor_status != AttendanceCorrectionRequest.SupervisorStatus.PENDING:
            return Response({"detail": "This correction is not awaiting supervisor approval."}, status=400)

        correction.supervisor_status = AttendanceCorrectionRequest.SupervisorStatus.APPROVED
        correction.supervisor_reviewed_at = timezone.now()
        correction.supervisor_comment = request.data.get("comment", "")
        correction.save()
        notifications.notify_supervisor_approved(correction)
        return Response(AttendanceCorrectionRequestSerializer(correction).data)

    @action(detail=True, methods=["post"], url_path="supervisor-reject")
    def supervisor_reject(self, request, pk=None):
        correction = self.get_object()
        if not self._can_act_as_supervisor(request, correction):
            return Response({"detail": "Not authorized to act on this correction."}, status=403)
        if correction.supervisor_status != AttendanceCorrectionRequest.SupervisorStatus.PENDING:
            return Response({"detail": "This correction is not awaiting supervisor approval."}, status=400)

        # Rejection at the supervisor stage is terminal — it never reaches HR.
        correction.supervisor_status = AttendanceCorrectionRequest.SupervisorStatus.REJECTED
        correction.supervisor_reviewed_at = timezone.now()
        correction.supervisor_comment = request.data.get("comment", "")
        correction.status = AttendanceCorrectionRequest.Status.REJECTED
        correction.reviewed_at = timezone.now()
        correction.save()
        notifications.notify_rejected(correction, stage="supervisor")
        return Response(AttendanceCorrectionRequestSerializer(correction).data)

    @action(detail=True, methods=["post"], permission_classes=[IsHRManagerOrAbove])
    def approve(self, request, pk=None):
        correction = self.get_object()
        if correction.supervisor_status == AttendanceCorrectionRequest.SupervisorStatus.PENDING:
            return Response({"detail": "Awaiting supervisor approval first."}, status=400)

        record, _ = AttendanceRecord.objects.get_or_create(
            employee=correction.employee, date=correction.date
        )
        if correction.requested_clock_in:
            record.clock_in = correction.requested_clock_in
        if correction.requested_clock_out:
            record.clock_out = correction.requested_clock_out
        record.save()

        correction.status = AttendanceCorrectionRequest.Status.APPROVED
        correction.reviewed_by = getattr(request.user, "employee", None)
        correction.reviewed_at = timezone.now()
        correction.review_comment = request.data.get("comment", "")
        correction.attendance = record
        correction.save()
        notifications.notify_approved(correction)
        return Response(AttendanceCorrectionRequestSerializer(correction).data)

    @action(detail=True, methods=["post"], permission_classes=[IsHRManagerOrAbove])
    def reject(self, request, pk=None):
        correction = self.get_object()
        if correction.supervisor_status == AttendanceCorrectionRequest.SupervisorStatus.PENDING:
            return Response({"detail": "Awaiting supervisor approval first."}, status=400)

        correction.status = AttendanceCorrectionRequest.Status.REJECTED
        correction.reviewed_by = getattr(request.user, "employee", None)
        correction.reviewed_at = timezone.now()
        correction.review_comment = request.data.get("comment", "")
        correction.save()
        notifications.notify_rejected(correction, stage="hr")
        return Response(AttendanceCorrectionRequestSerializer(correction).data)


class QRTokenViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = QRToken.objects.select_related("branch", "work_shift").all()
    serializer_class = QRTokenSerializer
    permission_classes = [IsHRManagerOrAbove]
    filterset_fields = ["branch", "is_active"]

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def verify(self, request):
        token_value = request.data.get("token")
        now = timezone.now()
        try:
            token = QRToken.objects.get(
                token=token_value, is_active=True, valid_from__lte=now, valid_until__gte=now
            )
        except QRToken.DoesNotExist:
            return Response({"detail": "Invalid or expired QR token."}, status=400)

        employee = getattr(request.user, "employee", None)
        if not employee:
            return Response({"detail": "No employee profile linked to this user."}, status=400)

        record, _ = AttendanceRecord.objects.get_or_create(
            employee=employee, date=now.date(), defaults={"method": AttendanceRecord.Method.QR}
        )
        if not record.clock_in:
            record.clock_in = now
            record.method = AttendanceRecord.Method.QR
            _evaluate_clock_in(record, employee, now)
            punch_event = PunchLog.Event.IN
        else:
            record.clock_out = now
            _evaluate_clock_out(record, employee, now)
            punch_event = PunchLog.Event.OUT
        record.save()
        PunchLog.objects.get_or_create(
            employee=employee,
            device=None,
            timestamp=now,
            defaults={"event": punch_event, "method": AttendanceRecord.Method.QR},
        )
        return Response(AttendanceRecordSerializer(record).data)

from rest_framework import serializers

from apps.attendance.models import (
    AttendanceCorrectionRequest,
    AttendanceRecord,
    AttendanceSettings,
    BreakRecord,
    Device,
    PunchLog,
    QRToken,
    SyncAgent,
    SyncEvent,
)


class DeviceSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True, default=None)

    class Meta:
        model = Device
        fields = "__all__"


class PunchLogSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    device_name = serializers.CharField(source="device.name", read_only=True, default=None)

    class Meta:
        model = PunchLog
        fields = "__all__"


class BreakRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreakRecord
        fields = "__all__"


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)
    department_name = serializers.CharField(
        source="employee.department.name", read_only=True, default=None
    )
    shift_name = serializers.CharField(source="employee.work_shift.name", read_only=True, default=None)
    device_name = serializers.CharField(source="device.name", read_only=True, default=None)
    breaks = BreakRecordSerializer(many=True, read_only=True)
    working_hours = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceRecord
        fields = "__all__"

    def get_working_hours(self, obj):
        if obj.clock_in and obj.clock_out:
            return round((obj.clock_out - obj.clock_in).total_seconds() / 3600, 2)
        return None

    def get_status(self, obj):
        if not obj.clock_in:
            return "ABSENT"
        return "LATE" if obj.is_late else "PRESENT"


class AttendanceCorrectionRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    reviewed_by_name = serializers.CharField(
        source="reviewed_by.full_name", read_only=True, default=None
    )
    supervisor_name = serializers.CharField(source="supervisor.full_name", read_only=True, default=None)
    current_stage = serializers.CharField(read_only=True)

    class Meta:
        model = AttendanceCorrectionRequest
        fields = "__all__"
        read_only_fields = [
            "employee",
            "status",
            "reviewed_by",
            "reviewed_at",
            "supervisor",
            "supervisor_status",
            "supervisor_reviewed_at",
        ]


class AttendanceSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceSettings
        fields = "__all__"


class QRTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRToken
        fields = "__all__"


class SyncAgentSerializer(serializers.ModelSerializer):
    """Never exposes key_hash — the raw key is only ever returned once, at
    creation/regeneration time, directly from the view (not via this serializer)."""

    branch_name = serializers.CharField(source="branch.name", read_only=True, default=None)

    class Meta:
        model = SyncAgent
        fields = ["id", "name", "branch", "branch_name", "key_prefix", "is_active", "last_seen_at", "created_at"]
        read_only_fields = ["key_prefix", "last_seen_at", "created_at"]


class SyncEventSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.name", read_only=True, default=None)

    class Meta:
        model = SyncEvent
        fields = "__all__"

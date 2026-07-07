from rest_framework import serializers

from apps.attendance.models import (
    AttendanceCorrectionRequest,
    AttendanceRecord,
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
    device_name = serializers.CharField(source="device.name", read_only=True, default=None)
    breaks = BreakRecordSerializer(many=True, read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = "__all__"


class AttendanceCorrectionRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    reviewed_by_name = serializers.CharField(
        source="reviewed_by.full_name", read_only=True, default=None
    )

    class Meta:
        model = AttendanceCorrectionRequest
        fields = "__all__"
        read_only_fields = ["status", "reviewed_by", "reviewed_at"]


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

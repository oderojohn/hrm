from rest_framework import serializers

from apps.system_settings.models import (
    BackupRecord,
    EmailSettings,
    SMSGatewaySettings,
    SystemSetting,
)


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = "__all__"


class EmailSettingsSerializer(serializers.ModelSerializer):
    smtp_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    is_configured = serializers.SerializerMethodField()

    class Meta:
        model = EmailSettings
        fields = "__all__"

    def get_is_configured(self, obj):
        return bool(obj.smtp_host and obj.smtp_username and obj.smtp_password)

    def update(self, instance, validated_data):
        # PATCH with no password (or blank) keeps the existing one — the
        # frontend never receives the real password back, so it can't
        # round-trip it; only overwrite when a new value is actually sent.
        if not validated_data.get("smtp_password"):
            validated_data.pop("smtp_password", None)
        return super().update(instance, validated_data)


class SMSGatewaySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSGatewaySettings
        fields = "__all__"


class BackupRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupRecord
        fields = "__all__"

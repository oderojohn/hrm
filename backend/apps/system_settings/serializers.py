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
    class Meta:
        model = EmailSettings
        fields = "__all__"


class SMSGatewaySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSGatewaySettings
        fields = "__all__"


class BackupRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupRecord
        fields = "__all__"

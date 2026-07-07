from django.contrib import admin

from apps.system_settings.models import (
    BackupRecord,
    EmailSettings,
    SMSGatewaySettings,
    SystemSetting,
)


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "description")
    search_fields = ("key", "description")


@admin.register(EmailSettings)
class EmailSettingsAdmin(admin.ModelAdmin):
    list_display = ("smtp_host", "smtp_port", "smtp_username", "use_tls", "from_email")


@admin.register(SMSGatewaySettings)
class SMSGatewaySettingsAdmin(admin.ModelAdmin):
    list_display = ("provider_name", "sender_id", "is_enabled")


@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    list_display = ("file_name", "status", "triggered_by", "size_bytes", "created_at")
    list_filter = ("status",)
    search_fields = ("file_name", "notes")
